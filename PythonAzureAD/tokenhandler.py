import jwt
import json
import urllib.request
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

'''
Token handler for APIs
'''


class TokenHandler:
    def __init__(self, pub_url, resource):
        self.pub_url = pub_url
        self.resource = resource
        self.refresh_keys()

    def refresh_keys(self):
        # Refresh the public keys
        with urllib.request.urlopen(self.pub_url) as url:
            self.key_data = json.loads(url.read().decode())

    def validate_token(self, access_token):
        # Check the header of our token thumbprint
        try:
            thumbprint = jwt.get_unverified_header(access_token)['x5t']
        except Exception as e:
            raise Exception("parsing error: " + str(e))

        try:
            matching_key = next(key for key in self.key_data['keys'] if key['x5t'] == thumbprint)
        except:
            # Just in case there has been a key rollover, we refresh the public keys and try again
            # See https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-signing-key-rollover
            self.refresh_keys()
            try:
                matching_key = next(key for key in self.key_data['keys'] if key['x5t'] == thumbprint)
            except Exception:
                raise Exception('thumbprint does not match public keys')

        # Format a certificate
        x5c_string = matching_key['x5c'][0]
        PEMSTART = "-----BEGIN CERTIFICATE-----\n"
        PEMEND = "\n-----END CERTIFICATE-----\n"
        cert_str = PEMSTART + x5c_string + PEMEND

        cert_obj = load_pem_x509_certificate(cert_str.encode(),
                                             default_backend())
        public_key = cert_obj.public_key()

        # Support for audience claims that has an 'spn' prefix
        spn = ""
        unverified = jwt.decode(access_token, verify=False)
        if unverified['aud'].startswith("spn:"):
            spn = "spn:"

        # Attempt to decode the token with our key
        return jwt.decode(access_token,
                          public_key,
                          algorithms=['RS256'],
                          audience=spn + self.resource)
