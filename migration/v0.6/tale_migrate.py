import tempfile
from girder.models.api_key import ApiKey
from girder.exceptions import ValidationException, GirderException
from girder.models.folder import Folder
from girder.models.item import Item
from girder.models.file import File
from girder.models.upload import Upload
from girder.models.user import User
from girder.plugins.wholetale.models.tale import Tale
from girder.plugins.wholetale.utils import getOrCreateRootFolder
from girder.plugins.wholetale.constants import CATALOG_NAME
from bson import ObjectId
import os

CAT_ROOT = getOrCreateRootFolder(CATALOG_NAME)
"""
This script migrates v0.5 Tales to the v0.6 workspace format.
* Registered datasets are added to  tale[dataSets] 
* Previously snapshotted files are moved to the workspace
"""

print("Beginning v0.6 Tale migration")

bad_tales = 0
for tale in list(Tale().find()):
    if str(tale['_id']) in {'598bbc1f4264d20001e170b1', '5be57c6b6141bc0001cc43dc',
                            '5b71cb9141453200015fd753', '5c018a216141bc0001cc89a4',
                            '5ad4eb52f4b80b00018d92e1'}: # Logan's Tale
        continue
    try:
        user = User().load(tale.get('creatorId'), force=True)
    except ValidationException:
        user = None

    print("\n\nMigrating Tale {_id} {title} by {authors}".format(**tale))

    # Create the workspace folder
    workspace = Tale().createWorkspace(tale, creator=user)

    dataSet = tale.get('dataSet', [])
    bad_tale = False

    # Only migrate if tale[folderId] present
    if 'folderId' in tale and tale['folderId'] is not None:
        data_folder = Folder().load(tale['folderId'], force=True)
        for folder in Folder().childFolders(data_folder, parentType='folder', force=True):
            if 'meta' in folder:
                print('\tFound registered data {}, adding to dataSet'.format(folder['name']))
                orig = Folder().findOne({
                    'parentId': CAT_ROOT['_id'],
                    'meta.identifier': folder['meta']['identifier']
                })
                if orig:
                    dataSet.append({
                        'itemId': str(orig['_id']),
                        'mountPath': folder['name'],
                        '_modelType': 'folder'
                    })
                    print('\tRemoving folder {}'.format(folder['name']))
                    Folder().remove(folder)
                else:
                    print("\tNeed to register folder {}".format(folder['meta']['identifier']))
                    bad_tale = True
            else:
                print("\tFound user folder {}, moving contents to workspace".format(folder['name']))

                for (path, fobj) in Folder().fileList(
                          folder, user=user, subpath=True, data=False):
                    try:
                        print('\tMoving file {}'.format(path))
                        parentPath = os.path.dirname(path)
                        parent = workspace
                        if parentPath:
                            dirs = parentPath.split(os.sep)
                            for d in dirs:
                                 try:
                                     parent = Folder().createFolder(parent=parent, name=d,
                                         parentType='folder', creator=user, reuseExisting=True)
                                 except FileExistsError:
                                     pass
                        if 'linkUrl' in fobj:
                            print('\tFound registered file {}, adding to dataSet'.format(fobj['linkUrl']))
                            found = False;
                            for f in File().find({'linkUrl': fobj['linkUrl']}):
                                fitem = Item().load(f['itemId'], force=True)
                                if fitem and fitem['baseParentId'] == CAT_ROOT['baseParentId']:
                                    dataSet.append({
                                        'itemId': str(fitem['_id']),
                                        'mountPath': path,
                                        '_modelType': 'file'
                                    })
                                    found = True
                            if not found:
                                print("\tNeed to register file {}".format(fobj['linkUrl']))
                                bad_tale = True
                        else:
                            print('\tFound user file {}, adding to dataSet'.format(fobj['name']))
                            with tempfile.TemporaryFile() as fp:
                                for chunk in File().download(fobj)():
                                    fp.write(chunk)
                                size = fp.tell()
                                fp.seek(0)
                                print('\tUploading file {} to {}'.format(fobj['name'], parent['name']))
                                Upload().uploadFromFile(
                                    fp, size=size, name=fobj['name'], parentType='folder',
                                    parent=parent, user=user
                                )
                    except GirderException:
                        print('Failed to download/upload {} in {} ({})'.format(fobj['name'], tale['title'], tale['_id']))
                        pass
                print('\tRemoving folder {}'.format(folder['name']))
                Folder().remove(folder)
                bad_tale = True
        for item in Folder().childItems(data_folder):
            files = list(Item().childFiles(item))
            if len(files) != 1:
                print("Item with multiple files. This should never happen...")
                print("  !!!! In Tale {_id} {title}".format(**tale))
                bad_tale = True
            if 'linkUrl' in files[0]:
                print('\tFound registered file {}, adding to dataSet'.format(files[0]['linkUrl']))
                found = False;
                for f in File().find({'linkUrl': files[0]['linkUrl']}):
                    fitem = Item().load(f['itemId'], force=True)
                    if fitem['baseParentId'] == CAT_ROOT['baseParentId']:
                        dataSet.append({
                            'itemId': str(fitem['_id']),
                            'mountPath': fitem['name'],
                            '_modelType': 'file'
                        })
                        found = True
                if found:
                    print("\tRemoving item {}".format(f['_id']))
                    Item().remove(item)
                else:
                    print("\tNeed to register file {}".format(files[0]['linkUrl']))
                    bad_tale = True
            else:
                fobj = files[0]
                print("\tFound user file {}, moving to workspace".format(fobj['name']))
                try:
                    with tempfile.TemporaryFile() as fp:
                        for chunk in File().download(fobj)():
                            fp.write(chunk)
                        size = fp.tell()
                        fp.seek(0)
                        Upload().uploadFromFile(
                            fp, size=size, name=fobj['name'], parentType='folder',
                            parent=workspace, user=user
                        )
                except GirderException:
                    print('\tFailed to download/upload {} in {} ({})'.format(fobj['name'], tale['title'], tale['_id']))
                    pass
                print("\tRemoving item {}".format(fobj['_id']))
                Item().remove(item)
        if bad_tale:
            bad_tales += 1
        else:
            del tale['folderId']
            tale['workspaceId'] = data_folder['_id']
            tale['dataset'] = dataSet
            Folder().remove(data_folder)

    else:
        print("\tNo folderId in Tale")

    Tale().save(tale)

print("TOTAL BAD TALES = {}".format(bad_tales))
