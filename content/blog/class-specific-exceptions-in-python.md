Title: Class-Specific Exceptions in Python
Date: 2014-01-01
Category: Code
Lang: en

For one of my recent projects (<a href="https://github.com/adewes/blitz-db">Blitz-DB</a>) I wanted to implement class-specific exceptions: Those are probably best-known from the Django framework, which defines `DoesNotExist` and `MultipleObjectsReturned` exceptions for each model class. I really like this exception model since it allows for very readable, straightforward code like this:

    :::python

    try:
        user = User.objects.get(id = 1)
    except User.DoesNotExist:
        #no user with this ID in the database...

So how can we implement this functionality in Python? The simplest way would be to just define two exceptions with those names and attach them to the base class from which all our model classes are derived, like this:

    :::python

    class DoesNotExist(BaseException):
        pass

    class MultipleObjectsReturned(BaseException):
        pass

    class Model(object):

        """
        This is the base class for all our models.
        """

        MultipleObjectsReturned = MultipleObjectsReturned
        ObjectDoesNotExist = ObjectDoesNotExist

    class User(Model):
        pass

    class Project(Model):
       pass

This will allow us to access the exceptions using `User.DoesNotExist` and `Project.DoesNotExist`. This was easy, right? Well, there's a problem with this approach, since `User.DoesNotExist` is the same class as `Project.DoesNotExist.` This can lead to problems when handling exceptions from different models in the same code block, e.g. like this:

    :::python

    try:
        user = User.objects.get(id = 1)
        project = Project.objects.get(user = user)
    except User.DoesNotExist:
        #handle user exception
    except Project.DoesNotExist:
        #handle project exception

Here, if the user query works as expected but the project query fails and throws `Project.DoesNotExist`, the wrong exception handler (i.e. the first one) will be executed, since the two exception classes are identical! Merde.

How can we fix that? Meta-classes, of course! To create class-specific exceptions, we just define a metaclass and associate it to our Model class. Like that, every time a new model class gets created, the __new__ function of the metaclass will get called. Within that method we can then simply create and inject class-specific exceptions into our models, like this:

    :::python

    class ModelMeta(type):

        """
        This meta-class injects class-dependent exceptions into classes derived (or identical) to Model.
        """

        def __new__(meta,name,bases,dct):

            #We create our exception classes

            class DoesNotExist(BaseException):
                pass

            class MultipleObjectsReturned(BaseException):
                pass

            #We bind them to the class dictionary
            dct['DoesNotExist'] = DoesNotExist
            dct['MultipleObjectsReturned'] = MultipleObjectsReturned

            #We return the modified class dictionary
            return type.__new__(meta, name, bases, dct)

    class Model(object):

        __metaclass__ == ModelMeta

Now, each class derived from Model will have a set of unique exception class attributes `DoesNotExist` and `MultipleObjectsReturned`, so that the following will hold:

    :::python

    class Person(Model):
        pass

    class Project(Model):
        pass

    assert Person.DoesNotExist != Project.DoesNotExist

Voila :)