Title: Building a Document-Oriented Database in Python
Date: 2015-01-01
Category: Code
Lang: en

Last week I released the first version of BlitzDB: A document-based, object-oriented database written entirely in Python. Blitz is intended as a "low-end" replacement for MongoDB for use cases where you need a document-oriented data store but do not want to rely on additional third-party software. Blitz provides MongoDB-like querying capabilities and has a range of <a href="http://blitz-db.readthedocs.org">interesting features</a>.

The code can be found on <a href="https://github.com/adewes/blitzdb">Github</a> and the documentation is hosted at <a href="http://blitz-db.readthedocs.org">ReadTheDocs</a>. A downloadable version can be obtained from <a href="https://pypi.python.org/pypi/blitzdb/0.1.2">PyPi</a>, e.g. using <strong>pip</strong> or <strong>easy_install</strong>.
<h2>Making it available</h2>
Making a library available on <a href="https://pypi.python.org/pypi/blitzdb">PyPi</a> (the Python package index) was actually remarkably easy: After signing up for an account there it suffices to write a simple<a href="https://github.com/adewes/blitzdb/blob/master/setup.py"> setup.py</a> file that uses the <strong>distutils</strong> package to generate a source distribution and upload it to PyPi, complete with all relevant meta-data and version information.
<h2>Documenting it</h2>
Having a good, comprehensive documentation is a must if you want other people to use your library. Fortunately, <a href="http://sphinx-doc.org/">sphinx</a> makes it really easy to do this: Just create a new project using `<strong>sphinx quickstart</strong>`, add some ReStructuredText files, automatically include existing documentation from your source and compile the whole thing, e.g. to a website or a PDF.

Publishing the resulting documentation online is even easier thanks to <a href="http://www.readthedocs.org">ReadTheDocs</a>: This amazing just asks for the URL of your git repository and then generates and publishes the whole documentation for you. Even better, it automatically builds and maintains the documentation for different version of your software (e.g. as specified by your git tags), so users will always be able to find the right version of the documentation. Last but not least, you can automatically trigger the build process using Github notifications, so your documentation will always be up-to-date.
<h2>Writing Blitz: Challenges &amp; Interesting Bits</h2>
On of the more challenging parts of writing Blitz was the implementation of the MongoDB-like query language, which allows you to write expressions such as
<pre lang="python">backend.filter(Actor,
             {
             'first_name' : {'$in' : ['Charles','Charlie']},
             '$or' :[{'year_of_birth' : {'$gt': 1880}},
                     {'year_of_birth' : {'$lt': 1930}] 
             }</pre>
I ended up using a combination of closures and recursion. Basically, a compiler function takes the query dict and returns a compiled query in the form of a function, which in turn accepts a query function as parameter. This query function accepts a key and an expression (which can be just a value or another function) and returns the store keys of all documents whose values for the given key match the given expression.

To clarify the whole concept a bit, let's have a look at the annotated version of the compiler function:
<pre lang="python">def compile_query(query):
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
        return query</pre>
As an example, for the query <strong>{'foo' : {'$in' : [1,2,3]}}</strong> this will return the following function:
<pre lang="python">def compiled_query(query_function):
    return _get(query_function,key = 'foo',expression = lambda index: _in(index,[1,2,3]))</pre>
Here, <strong>_get</strong> just calls the <strong>query_function</strong> for the given <strong>key</strong> and <strong>expression</strong>:
<pre lang="python">def _get(query_function,key = key,expression = compiled_expression):
    return query_function(key,expression)</pre>
The query function, in turn, takes the <strong>key</strong> and and the <strong>expression</strong> and returns a <strong>QuerySet</strong>, which contains the keys of all documents whose value of the <strong>[key]</strong> field matches the given <strong>expression</strong>:
<pre lang="python">def query_function(key,expression):
    qs =  QuerySet(self,cls,store,indexes[key].get_keys_for(expression))
    return qs</pre>
Note that the document keys are retrieved by the <strong>get_keys_for</strong> function of the corresponding index. This function will recognize that <strong>expression</strong> is callable (in our case it is <strong>lambda index: _in(index, [1,2,3])</strong>) and will call it with itself as a parameter. The returned list of keys will then be used to construct a <strong>QuerySet</strong>. <strong>_in(index,expression)</strong> performs the actual <strong>$in</strong> operation that we're looking for:
<pre lang="python">def in_query(expression):

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

    return _in</pre>
The total calling sequence for the query is the following:
<ol>
    <li>We call <strong>compiled_query</strong> with <strong>query_function</strong> as an argument</li>
    <li><strong>compiled_query</strong> calls <strong>_get</strong> to retrieve all documents for the given <strong>key</strong> and <strong>expression</strong>.</li>
    <li><strong>_get</strong> calls <strong>query_function</strong> with the compiled <strong>_in</strong> query as an argument</li>
    <li><strong>query_function</strong> calls <strong>index.get_keys_for</strong> with the <strong>_in</strong> function as argument</li>
    <li><strong>index.get_keys_for</strong> calls <strong>_in</strong> with itself as argument</li>
    <li><strong>_in</strong> retrieves all matching document keys for the query (<strong>[1,2,3]</strong>) from the index and returns their store keys.</li>
    <li><strong>query_function</strong> constructs a <strong>QuerySet</strong> from these store keys and returns it to <strong>_get</strong>.</li>
    <li><strong>_get</strong> returns it to <strong>compiled_query</strong></li>
    <li><strong>compiled_query</strong> returns it to the user</li>
</ol>
This method is extremely flexible and allows us to easily include new directives by simply defining new query functions. Currently, Blitz already supports the <strong>$and, $or, $all, $gt, $gte, $lt, $lte, $eq, $ne, $not </strong>and<strong> $in</strong> directives, which behave exactly the same way as in MongoDB.
<h2>Next Steps</h2>
On of the next items on my To-Do list is to add support for SQL-Alchemy based backends, which would allow users to create a document-oriented database on top oF relational databases such as MySQL or PostgreSQL. Another high priority is the improvement of the indexing mechanism of the file-based backend, especially the introduction of incremental writes of index values to disk (currently, each commit rewrites the whole index file to disk, which obviously isn't very scalable).