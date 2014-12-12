# -*- coding: utf-8 -*-

import requests

def safe_get(urls, args_kwargs):
    '''
    safe_get uses the requests module's get
    method to attempt retrieving an HTTP(S)
    resource.  If one url fails, either because
    of a non-200 status code or other exception,
    the next url is requested.  

    Returns either the first successful retrieval
    or None if errors occur for every url in urls.

    Params:
        @urls: list of urls as strings
        @args_kwargs: list of 2-tuples (args, kwargs) to 
                      pass to requests get method
    '''
    if not args_kwargs:
      args_kwargs = [((), {})] * len(urls)
    for i, url in enumerate(urls):
        try:
            args, kwargs = args_kwargs[i] 
            r = requests.get(url, *args, **kwargs)
            if r.status_code == 200:
                return r.text
        except:
            pass
        
