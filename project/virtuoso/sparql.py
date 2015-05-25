#!/usr/bin/python
# -*- coding: utf8 -*-
from SPARQLWrapper import JSON, SPARQLWrapper


class SparQLVar(str):
    pass

class SparQLURI(SparQLVar):
    def sparql(self):
        return '<%s>' % super(SparQLURI, self).__str__()

class SparQLLiteral(SparQLVar):
    def sparql(self):
        return '"%s"' % super(SparQLLiteral, self).__str__()

class SparQL(object):
    def __init__(self, sparql_endpoint, default_graph_uri_name):
        self.sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setMethod('POST')
        sparql.addParameter('default-graph-uri', default_graph_uri_name)
        sparql.setReturnFormat(JSON)

    def create_graph(self, graph_uri):
        '''
        Create a new named graph with uri. Returns None.

        Example:
            op_create_graph(sparql,
                SparQLURI("http://www.example.com/"))
        '''

        assert isinstance(graph_uri, SparQLVar)
        self.sparql.setQuery('''
            CREATE GRAPH %s
            ''' % graph_uri.sparql())

        results = self.sparql.query().convert()

    def insert(self, subject, predict, object):
        '''
        Insert a tuple into graph. Returns None.

        Example:
            op_insert(sparql,
                SparQLURI("http://www.example.com/"),
                SparQLVar("ns:title"),
                SparQLVar("page"))
        '''
        assert isinstance(subject, SparQLVar)
        assert isinstance(predict, SparQLVar)
        assert isinstance(object, SparQLVar)

        self.sparql.setQuery('''
            INSERT DATA { %s %s %s }
            ''' % (subject.sparql(), predict.sparql(), object.sparql()))

        results = self.sparql.query().convert()

    def delete(self, subject, predict, object):
        '''
        Delete a triple from graph. Returns None.

        Since virtuoso have no feedback when deleting
        triples, we really can't tell how many triples
        we have deleted.

        Example:
            op_delete(sparql, 
                SparQLURI("http://www.example.com/about"),
                SparQLURI("http://www.ns.com/title"),
                SparQLLiteral("about page"))
        '''
        assert isinstance(subject, SparQLVar)
        assert isinstance(predict, SparQLVar)
        assert isinstance(object, SparQLVar)

        self.sparql.setQuery('''
            DELETE DATA { %s %s %s }
            ''' % (subject.sparql(), predict.sparql(), object.sparql()))

        results = self.sparql.query().convert()

    def query(self, subject=None, predict=None, object=None):
        '''
        Query the graph. Returns a generator of all
        matched queries.

        For simplcity, we preclude all datatypes in
        SPARQL except literals.

        Example:
            op_delete(sparql, 
                subject=SparQLURI("http://www.example.com/about"))
        '''

        bindings = []
        if subject is None:
            bindings.append({
                'constant': False,
                'binding': 's'
                })
        else:
            assert isinstance(subject, SparQLVar)
            bindings.append({
                'constant': True,
                'value': subject
                })
        if predict is None:
            bindings.append({
                'constant': False,
                'binding': 'p'
                })
        else:
            assert isinstance(predict, SparQLVar)
            bindings.append({
                'constant': True,
                'value': predict
                })
        if object is None:
            bindings.append({
                'constant': False,
                'binding': 'o'
                })
        else:
            assert isinstance(object, SparQLVar)
            bindings.append({
                'constant': True,
                'value': object
                })

        where_clause = []
        for i in bindings:
            if i['constant']:
                where_clause.append(i['value'].sparql())
            else:
                where_clause.append('?%s' % i['binding'])

        self.sparql.setQuery('''
            SELECT * WHERE { %s }
            ''' % ' '.join(where_clause))

        results = self.sparql.query().convert()
        for result in results['results']['bindings']:
            ret = []
            for i in bindings:
                if i['constant']:
                    ret.append(i['value'])
                else:
                    binding = i['binding']
                    value_type = result[binding]['type']
                    value = result[binding]['value']
                    if value_type == 'uri':
                        ret.append(SparQLURI(value))
                    else:
                        ret.append(SparQLLiteral(value.encode('utf8')))

            yield (ret[0], ret[1], ret[2])
