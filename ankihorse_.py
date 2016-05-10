from ankihorse import autopicture
from ankihorse import autovoice

autopicture.initialise\
        ( name='Japanese Autopicture'
        , source_field='English'
        , target_field='Picture'
        , model_name_substring='japanese'
        ) 

autovoice.initialise\
        ( name='Japanese Autovoice'
        , language='japanese'
        , source_field='Kana'
        , target_field='Voice'
        , model_name_substring='japanese'
        ) 
