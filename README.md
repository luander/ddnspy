# ddnspy
Dynamic DNS written in Python
Supports Cloudflare DNS

## Running

```bash
docker run -e CLOUDFLARE_API_KEY=$CLOUDFLARE_API_KEY ddnspy <hostname>
```

## Container signing public verification key
```
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEbFqp4dFJhoAX5IKvOHhX53wpR2kG
AdFiIMQMlwnpjET5T8MAVn/1dPV4FOuP0wXb41dr5n0EUPLHjfroagb66g==
-----END PUBLIC KEY-----
```