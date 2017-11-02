graceTimeOut = "10s"
debug = false
checkNewVersion = false
logLevel = "WARN"

# If set to true invalid SSL certificates are accepted for backends.
# Note: This disables detection of man-in-the-middle attacks so should only be used on secure backend networks.
# Optional
# Default: false
# 
# InsecureSkipVerify = true

defaultEntryPoints = ["http", "https"]

[entryPoints]
  [entryPoints.http]
  address = ":80"
  [entryPoints.https]
  address = ":443"
  [entryPoints.https.tls]

[acme]
email = "bgates@microsoft.com"   # FIXME
storage = "/acme/acme.json"
entryPoint = "https"
acmeLogging = true
onDemand = true
# Enable certificate generation on frontends Host rules. This will request a certificate from Let's Encrypt for each frontend with a Host rule.
# For example, a rule Host:test1.traefik.io,test2.traefik.io will request a certificate with main domain test1.traefik.io and SAN test2.traefik.io.
#
# Optional
#
# OnHostRule = true
# caServer = "https://acme-staging.api.letsencrypt.org/directory"

[web]
address = ":8080"

  
[docker]
endpoint = "unix:///var/run/docker.sock"
domain = "${domain}"
watch = true
exposedbydefault = true
swarmmode = true