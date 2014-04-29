import json
from os import environ

from eve import Eve
from eve.io.mongo import Validator

from settings import API_NAME, URL_PREFIX, requests, resources


class KeySchemaValidator(Validator):
    def _validate_keyschema(self, schema, field, dct):
        "Validate all keys of dictionary `dct` against schema `schema`."
        for key, value in dct.items():
            self._validate_schema(schema, key, value)

api = Eve(API_NAME, validator=KeySchemaValidator)


def add_document(resource, document):
    "Add a new document to the given resource."
    return api.test_client().post('/' + URL_PREFIX + '/' + resource,
                                  data=json.dumps(document),
                                  content_type='application/json')


def delete_documents(resource):
    "Delete all documents of the given resource."
    return api.test_client().delete('/' + URL_PREFIX + '/' + resource)


def register_resource(resource, schema, source, filt):
    """Register a new resource with the given schema and filter. This creates
    a new endpoint for the resource, whereas documents are stored in the source
    collection and a filter is applied.

    .. note:: This method calls Flask's add_url_rule under the hood, which
        raises an AssertionError in debugging mode when used after the first
        request was served."""
    api.register_resource(resource, {'item_title': resource,
                                     'schema': schema,
                                     'datasource': {'source': source,
                                                    'filter': filt}})


def register_resources(resources, conf):
    "Add existing resources as API resources."
    for res in resources:
        if 'endpoint' in res:
            schema = conf['schema']
            schema.update(res['fields'])
            register_resource(res['endpoint'], schema, conf['source'],
                              {conf['key']: res[conf['key']]})

register_services = lambda d: register_resources(d, requests)
register_facilities = lambda d: register_resources(d, resources)


def add_services():
    "Add existing services as API resources."
    with api.app_context():
        register_services(api.data.driver.db['services'].find())


def add_facilities():
    "Add existing facilities as API resources."
    with api.app_context():
        register_facilities(api.data.driver.db['facilities'].find())

# Register hook to add resource for service when inserted into the database
# FIXME: this hook fails in debug mode due an AssertionError raised by Flask
api.on_insert_services += register_services
api.on_insert_facilities += register_facilities
add_services()
add_facilities()


def main():
    # Heroku support: bind to PORT if defined, otherwise default to 5000.
    if 'PORT' in environ:
        port = int(environ.get('PORT'))
        host = '0.0.0.0'
    else:
        port = 5000
        host = '127.0.0.1'
    api.run(host=host, port=port)

if __name__ == '__main__':
    main()
