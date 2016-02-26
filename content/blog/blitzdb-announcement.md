Title: Building a Document-Oriented Database in Python
Date: 2015-01-01
Category: Code
Lang: en

Last week I released the first version of BlitzDB: A document-based, object-oriented database written entirely in Python. Blitz is intended as a "low-end" replacement for MongoDB for use cases where you need a document-oriented data store but do not want to rely on additional third-party software. Blitz provides MongoDB-like querying capabilities and has a range of <a href="http://blitzdb.readthedocs.org">interesting features</a>.

The code can be found on <a href="https://github.com/adewes/blitzdb">Github</a> and the documentation is hosted at <a href="http://blitz-db.readthedocs.org">ReadTheDocs</a>. A downloadable version can be obtained from <a href="https://pypi.python.org/pypi/blitzdb/0.1.2">PyPi</a>, e.g. using `pip` or `easy_install`.

<h2>Making it available</h2>

Making a library available on <a href="https://pypi.python.org/pypi/blitzdb">PyPi</a> (the Python package index) was actually remarkably easy: After signing up for an account there it suffices to write a simple<a href="https://github.com/adewes/blitzdb/blob/master/setup.py"> setup.py</a> file that uses the `distutils` package to generate a source distribution and upload it to PyPi, complete with all relevant meta-data and version information.
<h2>Documenting it</h2>
Having a good, comprehensive documentation is a must if you want other people to use your library. Fortunately, <a href="http://sphinx-doc.org/">sphinx</a> makes it really easy to do this: Just create a new project using ``sphinx quickstart``, add some ReStructuredText files, automatically include existing documentation from your source and compile the whole thing, e.g. to a website or a PDF.

Publishing the resulting documentation online is even easier thanks to <a href="http://www.readthedocs.org">ReadTheDocs</a>: This amazing just asks for the URL of your git repository and then generates and publishes the whole documentation for you. Even better, it automatically builds and maintains the documentation for different version of your software (e.g. as specified by your git tags), so users will always be able to find the right version of the documentation. Last but not least, you can automatically trigger the build process using Github notifications, so your documentation will always be up-to-date.

<h2>Writing Blitz: Challenges &amp; Interesting Bits</h2>

On of the more challenging parts of writing Blitz was the implementation of the MongoDB-like query language, which allows you to write expressions such as

    :::python

    backend.filter(Actor,
         {
         'first_name' : {'$in' : ['Charles','Charlie']},
         '$or' :[{'year_of_birth' : {'$gt': 1880}},
                 {'year_of_birth' : {'$lt': 1930}] 
         })

I ended up using a combination of closures and recursion. Basically, a compiler function takes the query dict and returns a compiled query in the form of a function, which in turn accepts a query function as parameter. This query function accepts a key and an expression (which can be just a value or another function) and returns the store keys of all documents whose values for the given key match the given expression.

To clarify the whole concept a bit, let's have a look at the annotated version of the compiler function:

    :::python

    def compile_query(query):
        if isinstance(query,dict):
            expressions = []
            #go through all key-value pairs of the dict
            for key,value in query.items():
                #is this a special dircective?
                if key.startswith('$'):
                    #query_funcs contains a list of generators for all expressions that we support (see example below)
                    if not key in query_funcs:
                        raise AttributeError("Invalid operator: %s" % key)
                    #call the query generator function with the given value and append it to the list of expressionbs
                    expressions.append(query_funcs[key](value))
                else:
                    expressions.append(filter_query(key,value))
            #if we have more than one expression, return an implicit AND query, if not just return a callable function
            # that evaluates the query
            if len(expressions) &gt; 1:
                return and_query(expressions) 
            else: 
                return expressions[0] if len(expressions) else lambda query_function : query_function(None,None)
        else:
            return query

As an example, for the query `{'foo' : {'$in' : [1,2,3]}}` this will return the following function:

    :::python

    def compiled_query(query_function):
        return _get(query_function,key = 'foo',expression = lambda index: _in(index,[1,2,3]))

Here, `_get` just calls the `query_function` for the given `key` and `expression`:

    :::python

    def _get(query_function,key = key,expression = compiled_expression):
        return query_function(key,expression)</pre>

The query function, in turn, takes the `key` and and the `expression` and returns a `QuerySet`, which contains the keys of all documents whose value of the `[key]` field matches the given `expression`:

    :::python

    def query_function(key,expression):
        qs =  QuerySet(self,cls,store,indexes[key].get_keys_for(expression))
        return qs

Note that the document keys are retrieved by the `get_keys_for` function of the corresponding index. This function will recognize that `expression` is callable (in our case it is `lambda index: _in(index, [1,2,3])`) and will call it with itself as a parameter. The returned list of keys will then be used to construct a `QuerySet`. `_in(index,expression)` performs the actual `$in` operation that we're looking for:

    :::python

    def in_query(expression):

        #Return a function that contains the 'expression' variable as a closure (by setting it as a default parameter)
        def _in(index,expression = expression):
            #if the expression is callable, call it as a function, otherwise just take the value
            ev = expression() if callable(expression) else expression

            #if the evaluated value is not a list or a tuple, raise an exception.
            if not isinstance(ev,list) and not isinstance(ev,tuple):
                raise AttributeError("$in argument must be an iterable!")

            #Return the hashed values for each item in the list
            hashed_ev = [index.get_hash_for(v) for v in ev]

            #Create an empty set of store keys (the result set)
            store_keys = set()

            #Add all items that match at least one item from hashed_ev
            for value in hashed_ev:
                store_keys |= set(index.get_keys_for(value))

            #Return the result as a list
            return list(store_keys)

        return _in

The total calling sequence for the query is the following:

* We call `compiled_query` with `query_function` as an argument
* `compiled_query` calls `_get` to retrieve all documents for the given `key` and `expression`.
* `_get` calls `query_function` with the compiled `_in` query as an argument
* `query_function` calls `index.get_keys_for` with the `_in` function as argument
* `index.get_keys_for` calls `_in` with itself as argument
* `_in` retrieves all matching document keys for the query (`[1,2,3]`) from the index and returns their store keys.
* `query_function` constructs a `QuerySet` from these store keys and returns it to `_get`.
* `_get` returns it to `compiled_query`
* `compiled_query` returns it to the user

This method is extremely flexible and allows us to easily include new directives by simply defining new query functions. Currently, Blitz already supports the `$and, $or, $all, $gt, $gte, $lt, $lte, $eq, $ne, $not `and` $in` directives, which behave exactly the same way as in MongoDB.

<h2>Next Steps</h2>

On of the next items on my To-Do list is to add support for SQL-Alchemy based backends, which would allow users to create a document-oriented database on top oF relational databases such as MySQL or PostgreSQL. Another high priority is the improvement of the indexing mechanism of the file-based backend, especially the introduction of incremental writes of index values to disk (currently, each commit rewrites the whole index file to disk, which obviously isn't very scalable).