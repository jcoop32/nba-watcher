import hashlib
from flask import request, make_response

def jsonify_with_etag(data,  app):
    # 1. Dump data to JSON string using our fast provider
    json_str = app.json.dumps(data)

    # 2. Create a fingerprint (MD5 hash) of the content
    fingerprint = hashlib.md5(json_str.encode('utf-8')).hexdigest()

    # 3. Check if client already has this version
    if request.headers.get('If-None-Match') == fingerprint:
        # Return 304 Not Modified (Empty body)
        return make_response('', 304)

    # 4. If new, send full response with the fingerprint
    response = make_response(json_str)
    response.headers['ETag'] = fingerprint
    response.headers['Content-Type'] = 'application/json'
    return response


import orjson
from flask.json.provider import JSONProvider

# --- OPTIMIZATION: Custom High-Speed JSON Provider ---
class OrJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        # OPT_NAIVE_UTC handles datetime objects automatically (faster than default)
        return orjson.dumps(obj, option=orjson.OPT_NAIVE_UTC).decode()

    def loads(self, s, **kwargs):
        return orjson.loads(s)
