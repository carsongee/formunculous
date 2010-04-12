from django.core import urlresolvers
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

def redirect(to, *args, **kwargs):
    """
    Returns an HttpResponseRedirect to the apropriate URL for the arguments
    passed.
    
    The arguments could be:
    
    * A model: the model's `get_absolute_url()` function will be called.
    
    * A view name, possibly with arguments: `urlresolvers.reverse()` will
    be used to reverse-resolve the name.
    
    * A URL, which will be used as-is for the redirect location.
    
    By default issues a temporary redirect; pass permanent=True to issue a
    permanent redirect
    """
    if kwargs.pop('permanent', False):
        redirect_class = HttpResponsePermanentRedirect
    else:
        redirect_class = HttpResponseRedirect
        
    # If it's a model, use get_absolute_url()
    if hasattr(to, 'get_absolute_url'):
        return redirect_class(to.get_absolute_url())
    
    # Next try a reverse URL resolution.
    try:
        return redirect_class(urlresolvers.reverse(to, args=args, kwargs=kwargs))
    except urlresolvers.NoReverseMatch:
        # If this doesn't "feel" like a URL, re-raise.
        if '/' not in to and '.' not in to:
            raise
        
    # Finally, fall back and assume it's a URL
    return redirect_class(to)

