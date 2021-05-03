"""

Notes : This file is chunked in two parts :
    1. The first part loads the data from the DTS APIs registry and then concerts it into a traditional
        DTS collections response
    2. The second builds the flask app.

Developer : Thibault Clérice
"""

import json
import requests
import os.path
from urllib.parse import urljoin


def count_total_items(baseuri: str) -> int:
    """Counts total items available via a given DTS API.

    :param str baseuri: base URI of the DTS API.
    :return: Total number of items.
    :rtype: int

    """
    h = {"User-Agent": "DTS Client"}
    entry_request = requests.get(baseuri, headers=h)
    ENDPOINTS = entry_request.json()

    try:
        ROOT_COLLECTION = requests.get(
            urljoin(baseuri, ENDPOINTS["collections"]), headers=h
        ).json()
        total_items = sum(int(coll["totalItems"]) for coll in ROOT_COLLECTION["member"])
    # there are different reasons why the request above may fail
    # the service may, for example, provide a reply in a format different from
    # JSON
    except:
        total_items = None
    print(f"{baseuri}: total items {total_items}")
    return total_items


registry_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "registry.json"
)

with open(registry_file) as f:
    registry_raw = json.load(f)
print(registry_raw["endpoints"])
collection_jsonld = {
    "@context": {
        "@vocab": "https://www.w3.org/ns/hydra/core#",
        "dc": "http://purl.org/dc/terms/",
        "dts": "https://w3id.org/dts/api#",
        "foaf": "http://xmlns.com/foaf/0.1/",
    },
    "@id": "w3id.org/dts-registry",
    "@type": "Collection",
    "totalItems": len(registry_raw["endpoints"]),
    "title": "Distributed Text Services Registry",
    "dts:dublincore": {
        "dc:publisher": ["Distributed Text Services"],
    },
    "member": list(
        [
            dict(
                {
                    "@id": api["endpoint"],
                    "title": api["label"],
                    "@type": "EntryPoint",
                    "totalItems": count_total_items(
                        api["endpoint"]
                    ),  # Should we update this from time to time ?
                    "dts:dublincore": {
                        "dc:creator": {
                            "foaf:name": api["contact"]["name"],
                            "foaf:mbox": api["contact"]["email"],
                        },
                        "dc:description": "This API is in a(n) {}".format(
                            api["status"]
                        ),
                    },
                }
            )
            for api in registry_raw["endpoints"]
            if api.get("protocol", "dts") == "dts"
        ]
    ),
}

known_uris = set([api["endpoint"] for api in registry_raw["endpoints"]])

# Now The APP

from flask import Flask, jsonify, redirect, url_for, request
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)


@app.route("/")
def entry_point():
    """JSON LD Entrypoint

    :return: Entry point response
    """
    return jsonify(
        {
            "@context": "/dts/api/contexts/EntryPoint.jsonld",
            "@id": "/dts/api/",
            "@type": "EntryPoint",
            "collections": url_for(".collections"),
        }
    )


@app.route("/collections")
def collections():
    """Collections endpoint

    :return: Only the root collection and redirect
    """
    _id = request.args.get("id", None)
    if _id is None:
        return collection_jsonld
    elif _id in known_uris:
        return redirect(_id)
    else:
        return (
            jsonify(
                {
                    "@context": "http://www.w3.org/ns/hydra/context.jsonld",
                    "@type": "Status",
                    "statusCode": 404,
                    "title": "Unknown collection",
                    "description": "This collection is unknown.",
                }
            ),
            404,
        )
