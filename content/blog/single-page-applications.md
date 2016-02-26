Title: What I learned about building single-page applications
Date: 2016-01-01
Category: Code
Lang: en

In the last two years that I have worked on QuantifiedCode (QC) I learned a lot about developing SaaS applications. Building a solution for automated code analysis is probably at the upper end of the complexity scale when it comes to SaaS applications, especially since we did it with very little external funding. In addition, QC was the first API-driven single-page application that I wrote, my first "professional" software project and also one of the most complex pieces of software that I have worked on so far. Hence it's probably unnecessary to say that I would probably do some things differently today if I should write another app of that scale.

So, distilled from my humble experience here are my personal ten commandments of SaaS development:

Do API-centric design.

Before QC, all my web projects were realized as "traditional" client/server applications: The browser sends a request, the server retrieves the required data for a given page, renders it into a template and returns it to the user.

For QC, I decided to start with a REST API instead and implement the frontend as a single-page web application (using React.js). My motivation behind this was that I wasn't sure how we would deliver our data to the user: Delivery through a web application, an IDE plugin or even a desktop app were equally likely.

Looking back, I would take this decision again, and I even go so far as to say that by default you should start with an API and only choose other options if absolutely necessary. Why?
<ol>
    <li>Frontend technologies and devices keep changing rapidly. Single-page applications were still new and exotic five years ago but are becoming the norm these days. In addition, tablets and smartphones are taking over the (end-user) world and delivering a good user experience usually means building native apps for these devices. If you start with a traditional app where data gets rendered on the server-side you will have to build an API in addition as soon as you need to deliver the data onto another</li>
</ol>