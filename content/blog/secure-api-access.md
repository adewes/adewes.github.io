Title: Securing API calls made on behalf of a user from an untrusted environment.
Date: 2015-01-01 10:20
Category: Code
Lang: en

Recently I worked on a <strong>desktop application</strong> that makes use of a third-party API (Dropbox, to be more precise) to retrieve data on behalf of a user. The API calls made by that application would work like this:
<ul>
    <li>When requesting data from the API, my<strong> desktop application</strong> would need to send an <strong>access token</strong> together with each HTTP request to the API server in order to prove that it has the correct access rights.</li>
    <li>To generate this <strong>access token</strong>, the user would first need to authorize my application using the usual web-based <strong>OAuth2</strong> authentication flow, which would be implemented on my backend website.</li>
    <li>After the user completed the authentication flow, my backend would ask the API server for the access token. It would then send that access token to the desktop application, where it could be used to make requests to the API server.</li>
</ul>
So far, so good. However, this way of doing things poses a security risk, since it allows the user (or a malicious entity having access to the user's computer) to extract the access token stored on the machine and misuse it for purposes not intended by my application (e.g. by exceeding the rate-limit or performing malicious requests). Pretty bad.

When I asked how to solve this problem on the <a href="https://www.dropboxforum.com/hc/communities/public/questions/201836019-How-to-make-sure-clients-dont-misuse-access-tokens-provided-to-them-">Dropbox developer forum</a>, the answer I got was to <strong>simply</strong> make all API calls on behalf of the user through my backend. This would of course allow me to keep the access token on the backend server and not reveal it to the user, but would be far from ideal for at least two reasons:
<ul>
    <li>It forces me to funnel all the API traffic through my own server, which exponentially increases the cost of running my service and creates a bottleneck through which all the user data needs to go.</li>
    <li>It does not allow my application to control or restrict the use of the provided access token by the user, which could be a security problem for the user if his access token would get stolen from his computer.</li>
</ul>
After thinking a bit about this, I think I found an easy, elegant way to solve the problem by using a bit of cryptography. The solution works like this:
<ul>
    <li>The API server would provide a new endpoint that can be called with the access token of a user, takes an URL -and possibly some additional data- as a parameter and returns a HMAC hash of that data, generated with a secret key that only the server knows.</li>
    <li>If the client application now wants to call a given endpoint on the API server, it would first ask my backend server for permission to do so by providing it with the URL of the endpoint it wants to call, and possibly some additional information that it would like to send along to the API server.</li>
    <li>After verifying that the API call is legitimate and conforms to the use of my application, my backend could then call the new endpoint on the API server using the access token obtained through OAuth2 and request a hash for the given endpoint and request data as given by the client. The server would then add the username of the client and an expiration date for the request to the provided data and hash everything using the HMAC algorithm. It would then transfer this hash with the additional data (in plain text) to the backend.</li>
    <li>The backend would then send the obtained hash with the additional data back to the client.</li>
    <li>The client could then send the hash it obtained together with the URL and the additional data to the API server.</li>
    <li>The API server in turn would rehash the data obtained from the client and verify that the hash matches the one it received from the client.</li>
    <li>If it does, the API call is treated as if it was made using the original access token of the user, and the results are returned to the client.</li>
</ul>
In short, this method allows to make authenticated calls to an API server on behalf of a user from an untrusted client, without exposing the required access token to that client. Here's a diagram explaining the process:<a href="http://www.andreas-dewes.de/en/wp-content/uploads/2015/02/api_flow.png"><img class="aligncenter size-large wp-image-313" src="http://www.andreas-dewes.de/en/wp-content/uploads/2015/02/api_flow-1024x576.png" alt="api_flow" width="660" height="371" /></a>

(please note that arrows going from the API server on the left to the client on the right represent information transferred directly between these two, and NOT transmitted through the backend server)

This method has several advantages:
<ul>
    <li>The backend does not need to share the access token with the untrusted client</li>
    <li>The backend can verify each individual request of the client, which improves security and allows for more fine-grained access control than would be possible when handing over the access token to the client.</li>
    <li>The actual request data is transferred directly from the client to the API server, without passing through our backend, saving cost and again improving security.</li>
    <li>The API server does not need to store any additional data on the permissions that it grants, since everything necessary to validate a given request is contained in the HMAC hash and the plain text that gets passed from the client to the server.</li>
    <li>We can make sure that the same hash cannot be used indefinitely to perform a given API request by including an expiration date in it, which would limit the validity of the hash to a short time period.</li>
</ul>
Personally, I would love to see this scheme implemented in APIs, since today many desktop applications rely on accessing an API on behalf of a given user and a given third-party application. What do you think?

The inspiration for this technique came from a fascinating article by NeoSmart Technologies about "<a href="https://neosmart.net/blog/2015/using-hmac-signatures-to-avoid-database-writes/">life in a post-database world</a>".

I also posted a question about this problem on <a href="http://security.stackexchange.com/questions/81773/prevent-a-desktop-client-application-from-abusing-an-api-access-token-obtained-t/81778#81778">Security Stackexchange</a>.