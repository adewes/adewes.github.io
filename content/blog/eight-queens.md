Title: Solving the "Eight Queens" Problem in SQL
Date: 2015-02-01 10:20
Category: Code
Lang: en

Recently I tried wrapping my head around a little-known but quite powerful SQL feature: <a href="http://en.wikipedia.org/wiki/Hierarchical_and_recursive_queries_in_SQL">Common Table Expressions</a>, or CTE's.

These expressions allow us to write SQL queries that can make use of recursion to retrieve or
even modify data. Sounds cool? It is! But how does it work?

Actually, it's pretty straightforward: When writing a (recursive) CTE, we first formulate a "seed"
query that returns an initial set of rows. Then, we formulate another query which takes a virtual
table containing these rows as input and uses them to (possibly) produce more rows of the same
format, e.g. by performing more queries on the database. All these new rows are then fed back
to the same statement again in another step of the recursion, until no more new rows are returned.
This might sounds more complicated than it is, so let's have a look at a very simple example.
I present you the "hello, world!" of common-table-expressions:

    :::sql
    
    WITH RECURSIVE --this tells SQL that we want to define a recursive CTE
      cnt(x) AS ( --the name of the CTE, 'cnt'
          VALUES(1) --the initial SELECT (actually just a single value here)
        UNION ALL
          --the recursive query (will yield one additional row containing the value of x+1)
          SELECT x+1 FROM cnt WHERE x < 100 
      )
    SELECT x FROM cnt; --this will return the numbers from 1 to 100

As you can see, the seed query on line 3 produces a single row of data containing the value 1.
This row is then fed as input to the second query in line 5, which produces another row with the
value 2 and returns it. This process is repeated until x reaches 100, at which point the query
will no longer generate any results. The result of each query gets united with the previous ones
and thus produces a list of integers between 1 and 100. So far, so good!

If you're not yet that impressed with CTEs let me assure you that we can use them for much more
complex queries, especially when dealing with hierarchical data sets or graphs. In fact, CTEs are
so powerful that we can even "abuse" them for things they were never designed for.
Let's give it a try :)

<h2>CTE Hacking</h2>

When reading up on CTEs on the <a href="http://www.sqlite.org/lang_with.html">SQLite website</a>,
I discovered a neat little example at the bottom of the page, which uses them to calculate a
Mandelbrot set. Amazing! This really intrigued me so I wanted to see what other problems I
could solve using CTEs.

One of the first things that came to my mind was the famous "<a href="http://en.wikipedia.org/wiki/Eight_queens_puzzle">eight queens</a>" problem, which goes like this: On a chess board, arrange eight queens such that none of them
can attack another queen on the board. This well-studied problem has 92 solutions and has been
implemented in almost any computer language (when I attended Hacker-School, people from my batch
wrote implementations in Go, Rust, Python, Scala and even <a href="http://davidad.github.io/blog/2014/02/25/overkilling-the-8-queens-problem/">Assembler</a> - and <a href="http://acmonette.com/here-there-be-pydras.html">one</a> of us even "abused" the Python garbage collector for this task). But was there an implementation written in SQL? I checked <a href="http://rosettacode.org/wiki/N-queens_problem">RosettaCode</a>, and indeed found nothing! Challenge accepted :)
<h2>Eight Queens in SQL</h2>
So, let's start with some basics of the eight-queens problem: First, we need a way to encode a
solution, which consists of a number of queens arranged on a 8x8 chess board. A simple way to
encode the positions of the individual queens is to use a 64-byte string, where each character
in the string represents one of the 64 fields of the chessboard. Each field can then either
be empty, denoted by a dash '-', or contain a queen, denoted by a star '*'. 
The string `-------*--*-----*------------*---*----------*---------*----*----` would thus
represent the following board:

<table style="width: 100%; text-align: center;">
<tbody>
<tr>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>*</td>
</tr>
<tr>
<td>-</td>
<td>-</td>
<td>*</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
</tr>
<tr>
<td>*</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
</tr>
<tr>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>*</td>
<td>-</td>
<td>-</td>
</tr>
<tr>
<td>-</td>
<td>*</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
</tr>
<tr>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>*</td>
<td>-</td>
<td>-</td>
<td>-</td>
</tr>
<tr>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>*</td>
<td>-</td>
</tr>
<tr>
<td>-</td>
<td>-</td>
<td>-</td>
<td>*</td>
<td>-</td>
<td>-</td>
<td>-</td>
<td>-</td>
</tr>
</tbody>
</table>
Pretty easy. Now, to solve the eight queens problem using CTEs we need to write an SQL query that performs the following tasks:
<ol>
    <li>Generate an initial valid board.</li>
    <li>Add a queen to the board while making sure that the resulting board is still a valid one (i.e. not any two queens on it can attack each other).</li>
    <li>Repeat this until a valid board with eight queens is found.</li>
</ol>
Of course, ideally the algorithm should not only produce a single valid solution to the problem, but all 92. So let's get to work!

<strong>Please note</strong><em>: I will use the SQLite dialect here, but the code that I show is compatible with Postgres and possibly other SQL dialects as well.</em>

Generating an initial valid board state is trivial, since we can just take an empty board without any queens on it:

    :::sql

    SELECT '----------------------------------------------------------------',0

Here, we also add a '0' to the resulting row of our seed table, which is simply the number of queens on the board. The next thing that we need, is a list of board positions that we can use to generate new solution candidates. This can be done using a CTE as well, which in fact is just a modified version of our "hello, world!" example:

    :::python

    WITH RECURSIVE
     positions(i) as (
     VALUES(0)
     UNION SELECT ALL
     i+1 FROM positions WHERE i < 63
     )
    -- ... (more to follow)

This will generate a <em>positions</em> table containing the numbers between 0 and 63.

Now, we need a way to add a queen to an existing board state in order to produce a new board with more queens on it. For this, we can make use of SQL string functions: Assume we have a <em>solutions</em> table containing a list of boards with <em>n</em> queens. We can then perform the following SELECT operation to extend a board and produce boards with <em>n+1</em> queens from it:

    :::sql

    SELECT
      substr(board, 1, i) || '*' || substr(board, i+2),n_queens + 1 as n_queens
    FROM positions AS ps, solutions 
    WHERE substr(board,1,i) != '*'

This code performs a <span class="lang:default decode:true crayon-inline ">SELECT</span> operation over the <em>positions</em> and <em>solutions</em> tables, taking a <em>board</em> from the <em>solutions</em> table and a number <em>i</em> from the <em>positions</em> table and inserting a queen at the <em>i-th</em> position of the <em>board</em>. The <span class="lang:default decode:true crayon-inline ">WHERE</span>  condition in the query just makes sure that we don't add a queen at a position where we already have one on the board.

Unfortunately, the boards that we generate like this are not necessarily valid solutions to our problem, since we don't check yet whether any two queens on the new board could attack each other. To do this, we need another, slightly more complex <span class="lang:default decode:true crayon-inline ">WHERE</span>  condition, which looks like this:

    :::sql

    ---our previous SELECT query...
      WHERE substr(board,1,i) != '*'
      AND NOT EXISTS ( -- we only add the queen if the following result set is empty
     SELECT 1 FROM positions WHERE -- we loop through all positions
     substr(board,i+1,1) = '*' AND -- we check if there's a queen on this field
       (
       i % 8 = ps.i %8 OR --is the queen on the same column?
       cast(i / 8 AS INT) = cast(ps.i / 8 AS INT) OR --...or the same row?
       cast(i / 8 AS INT) + (i % 8) = cast(ps.i / 8 AS INT) + (ps.i % 8) OR
       cast(i / 8 AS INT) - (i % 8) = cast(ps.i / 8 AS INT) - (ps.i % 8)  --...or the same diagonal?
       )
     LIMIT 1 --if we find one single conflict we can immediately discard the solution
     ) 

Here we loop again over all the **positions i** on the board and check if there's a queen on
the corresponding field. If there is, we check if that "old" queen (which is at position 
*x*<sub>old</sub>= i % 8 , y<sub>old</sub></em> = floor(<em>i / 8</em>)) could attack the new 
queen that we'd like to add to the board, and which is at position (<em>x<sub>new</sub> = ps.i % 8, 
y<sub>new</sub></em> = floor(<em>ps.i / 8</em>) ). This is done by the four OR expressions in the
parenthesis, which check whether the queens are on the same column 
(<em>x<sub>old</sub> = x<sub>new</sub></em>), row (<em>y<sub>old</sub> = y<sub>new</sub></em>) 
or diagonal (<em>x<sub>old</sub> + y<sub>old</sub> = x<sub>new</sub>+y<sub>new</sub></em> or 
<em>x<sub>old</sub>-y<sub>old</sub> = x<sub>new</sub>-y<sub>new</sub></em>). If one of these 
conditions is met, the inner <span class="lang:default decode:true crayon-inline">SELECT</span> 
query will return a non-empty list and the ```NOT EXISTS```  condition will fail, resulting in the board being discarded. By the way, we don't have to perform this check for the queens that are already on the board because we started from a valid <em>board</em> state to begin with.

Now that's basically everything we need to solve the problem! Putting all of it together
yields the following, rather compact SQL statement:

    :::sql
    WITH RECURSIVE
    positions(i) as (
      VALUES(0)
      UNION SELECT ALL
      i+1 FROM positions WHERE i < 63
      ),
    solutions(board, n_queens) AS (
      SELECT '----------------------------------------------------------------', cast(0 AS bigint) 
        FROM positions
      UNION
      SELECT
        substr(board, 1, i) || '*' || substr(board, i+2),n_queens + 1 as n_queens
        FROM positions AS ps, solutions 
      WHERE n_queens < 8
        AND substr(board,1,i) != '*'
        AND NOT EXISTS (
          SELECT 1 FROM positions WHERE
            substr(board,i+1,1) = '*' AND
              (
                  i % 8 = ps.i %8 OR
                  cast(i / 8 AS INT) = cast(ps.i / 8 AS INT) OR
                  cast(i / 8 AS INT) + (i % 8) = cast(ps.i / 8 AS INT) + (ps.i % 8) OR
                  cast(i / 8 AS INT) - (i % 8) = cast(ps.i / 8 AS INT) - (ps.i % 8)
              )
          LIMIT 1
          ) 
     ORDER BY n_queens DESC --remove this for PostgreSQL
    )
    
    -- Perform a selector over the CTE to extract the solutions with 8 queens
    SELECT board,n_queens FROM solutions WHERE n_queens = 8;

The solutions are generated by performing a `SELECT` operation over the **solutions** CTE,
with a `WHERE` condition that only returns **boards** with 8 queens. Of course, by changing
this condition we can also retrieve solutions with fewer queens, or check that there
are no solutions with more than eight queens.

You might have noticed the `ORDER BY` 
clause on the inner `SELECT` statement:
Its purpose is to make sure that we perform a *depth-first* search of the solution
space, which means that we will first explore states with many queens before checking out states
with fewer ones. This search order will yield a first solution faster than when doing a
breadth-first search, but will not speed up the query when searching the whole solution space.

Now, the simplest way to run this SQL query is using *SQLite*, which added support
for CTEs in Version 3.8.3. Here's a simple Python script that creates an in-memory SQLite database
and runs the query on it:

    :::python
    #!/usr/bin/env python
    import sqlite3
    import sys
    conn = sqlite3.connect(':memory:')

    version = sqlite3.sqlite_version.split(".")
    if version[1] < 8 or version[2] < 3:
        print "Warning: Your SQLite version might be too old to run this query! You need at least 3.8.3."

    with open('eight_queens.sql','r') as script_file:
        sql_script = script_file.read()

    c = conn.cursor()

    DIM = 8

    print "Calculating solutions, please stand by..."

    result = c.execute(sql_script)

    cnt = 0
    for row in result:
        cnt+=1
        print "n".join([row[0][i*DIM:i*DIM+DIM] for i in range(len(row[0])/DIM)]),"n"

    assert cnt == 92

(there's a <a href="https://gist.github.com/adewes/5e5397b693eb50e67f07">Gist</a> with all the
required files; the script will warn you if your SQLite version is too old to run the query, btw).
On my machine, the query returns all 92 solutions of the eight-queens problem in less than 5
minutes, which is not very fast compared to other approaches but still impressive considering the
fact that we run it in a relational database :D Here's the (abbreviated) output of the script:


    Calculating solutions, please stand by...
    *-------
    ----*---
    -------*
    -----*--
    --*-----
    ------*-
    -*------
    ---*---- 

    *-------
    -----*--
    -------*
    --*-----
    ------*-
    ---*----
    -*------
    ----*--- 

    *-------
    ------*-
    ---*----
    -----*--
    -------*
    -*------
    ----*---
    --*----- 

    *-------
    ------*-
    ----*---
    -------*
    -*------
    ---*----
    -----*--
    --*----- 

    #... and so on ;)

You can also run the query on Postgres, in which case you first have to remove the 
`ORDER BY` statement from the inner `SELECT`, which currently is not
supported there. Since this forces us to do a breadth-first search of the solution space we have
to wait a little longer for a valid solution with eight queens to show up, but searching the entire
solution space takes just a few minutes as well. I didn't compare the actual performance of
Postgres with SQLite since that wasn't the goal of my little exercise, but if you should do
this feel free to send me the results and I'll include them here. Here's the output of the
Postgres query (in raw form):

                                  board                               | n_queens 
    ------------------------------------------------------------------+----------
     *-----------*----------*-----*----*-----------*--*---------*---- |        8
     *------------*---------*--*-----------*----*-----*----------*--- |        8
     *-------------*----*---------*---------*-*----------*-----*----- |        8
     *-------------*-----*----------*-*---------*---------*----*----- |        8
     -*---------*---------*---------*--*-----*-------------*-----*--- |        8
     -*----------*---------*-*---------*------------*-----*-----*---- |        8
     -*----------*---------*----*----*--------------*-----*----*----- |        8
     -*-----------*--*-------------*----*-----------*--*---------*--- |        8
     -*-----------*---------*--*-----*----------*----------*-----*--- |        8
     -*------------*---*----------*---------*----*---*----------*---- |        8
     -*------------*-----*----------**----------*---------*----*----- |        8
     -*-------------*-----*--*---------*---------*---------*----*---- |        8
     --*-----*-------------*-----*----------*-*---------*---------*-- |        8
     --*---------*----*-------------**-------------*----*---------*-- |        8
     --*---------*----*-------------*-----*-----*----------*-*------- |        8
     --*---------*---------*-*----------*-----*-------------*-----*-- |        8
     --*---------*----------*---*----*-------------*--*-----------*-- |        8
     --*----------*---*----------*----------**-------------*----*---- |        8
     --*----------*---*------------*-*----------*-----------*----*--- |        8
     --*----------*---*------------*-----*---*--------------*---*---- |        8
     --*----------*-----*----*--------------*----*---------*--*------ |        8
     --*----------*-----*-----*-------------*----*---------*-*------- |        8
     --*----------*---------**----------*----------*-----*----*------ |        8
     --*----------*---------**-----------*---------*--*---------*---- |        8
     --*----------*---------*-*---------*----*-------------*-----*--- |        8
     --*-----------*--*-------------*----*---*----------*---------*-- |        8
     --*-----------*--*-------------*-----*-----*----*-----------*--- |        8
     --*------------*---*----------*-*------------*---*----------*--- |        8
     ---*----*-----------*----------*-*------------*---*----------*-- |        8
     ---*----*-----------*----------*-----*----*-----------*--*------ |        8
     ---*-----*----------*----------*-----*--*---------*-----------*- |        8
     ---*-----*------------*---*----------*---------**-----------*--- |        8
     ---*-----*------------*---*----------*---------*----*---*------- |        8
     ---*-----*------------*-----*---*--------------*-----*----*----- |        8
     ---*-----*-------------*----*---------*-*---------*----------*-- |        8
     ---*-----*-------------*-----*--*---------*---------*---------*- |        8
     ---*---------*--*-----------*----*-------------*--*-----------*- |        8
     ---*---------*---------*-*------------*-*---------*---------*--- |        8
     ---*---------*---------*--*-----*-------------*-----*----*------ |        8
     ---*----------*-*--------------*----*----*-----------*----*----- |        8
     ---*----------*---*------------*-*----------*---*------------*-- |        8
     ---*----------*-----*----*-----------*--*---------*------------* |        8
     ---*----------*-----*-----*-----*------------*---------*-*------ |        8
     ---*-----------**---------*----------*---*------------*-----*--- |        8
     ---*-----------**-----------*---------*--*-----------*----*----- |        8
     ---*-----------*----*-----*-----*-------------*--*-----------*-- |        8
     ----*---*----------*---------*---------*-*------------*---*----- |        8
     ----*---*--------------*---*-----*------------*---*----------*-- |        8
     ----*---*--------------*-----*----*-----------*--*---------*---- |        8
     ----*----*---------*---------*---------*--*-----*-------------*- |        8
     ----*----*---------*----------*---*------------*-----*--*------- |        8
     ----*----*-----------*--*-------------*----*-----------*--*----- |        8
     ----*----*-------------**----------*----------*---*----------*-- |        8
     ----*-----*-----*------------*---------*-*---------*----------*- |        8
     ----*-----*-----*-------------*--*-------------*-----*-----*---- |        8
     ----*-----*------------*---*----------*-*------------*---*------ |        8
     ----*---------*-*---------*------------*-----*-----*-----*------ |        8
     ----*---------*-*----------*-----*-------------*-----*----*----- |        8
     ----*---------*--*---------*-----------**---------*----------*-- |        8
     ----*---------*--*-----------*----*-----*----------*-----------* |        8
     ----*---------*--*-----------*----*-----*--------------*---*---- |        8
     ----*---------*----*----*---------*------------*-----*---*------ |        8
     ----*----------*---*----*---------*----------*---*------------*- |        8
     ----*----------*---*----*-------------*--*-----------*----*----- |        8
     -----*--*-----------*----*-------------*--*-----------*----*---- |        8
     -----*---*------------*-*---------*---------*----------*---*---- |        8
     -----*---*------------*-*----------*-----------*----*-----*----- |        8
     -----*----*-----*-------------*-----*----------*-*---------*---- |        8
     -----*----*-----*--------------*---*-----*------------*-----*--- |        8
     -----*----*-----*--------------*----*----*---------*----------*- |        8
     -----*----*---------*---------*-*----------*-----*-------------* |        8
     -----*----*---------*----------**----------*-----*------------*- |        8
     -----*----*-----------*--*---------*-----------**-----------*--- |        8
     -----*----*-----------*--*-------------*----*---*----------*---- |        8
     -----*----*-----------*----*----*--------------*-*----------*--- |        8
     -----*-----*----*-----------*----------*-*------------*---*----- |        8
     -----*-----*-----*-------------*----*---------*-*---------*----- |        8
     -----*-----*----------*-*---------*---------*----*-------------* |        8
     -----*-----*----------*-*--------------*-*----------*-----*----- |        8
     -----*---------*-*---------*----*-------------*-----*-----*----- |        8
     ------*-*---------*------------*-----*-----*-----*----------*--- |        8
     ------*--*---------*----*--------------*----*-----*----------*-- |        8
     ------*--*-----------*----*-----*----------*-----------*----*--- |        8
     ------*---*-----*------------*---------*----*----*---------*---- |        8
     ------*---*------------*-*----------*---*------------*-----*---- |        8
     ------*----*-----*----------*----------**---------*----------*-- |        8
     ------*----*-----*-------------*-----*--*---------*---------*--- |        8
     ------*-----*-----*-----*------------*---------*-*---------*---- |        8
     -------*-*---------*----*-------------*-----*-----*----------*-- |        8
     -------*-*----------*-----*-----*-------------*----*---------*-- |        8
     -------*--*-----*------------*---*----------*---------*----*---- |        8
     -------*---*----*---------*----------*---*------------*-----*--- |        8
    (92 rows)

Anyway, I hope that I could convince you that common table expressions are a powerful tool
and can be used for all kinds of interesting hacks. Personally, I am also very happy that I
could add a new "SQL" entry to the <a href="http://rosettacode.org/wiki/N-queens_problem">RosettaCode</a>
page for the "n-queens" problem.
