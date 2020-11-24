# Python logger library

    Python versions 2.6+2.7+3.5 are supported
    
Logs format corresponds to the one described in **RFC 5424-5428**, but extended by multiline support. 
Supplying **url_encode=True** or **escape_rfc5424_special_chars=True** options will make resulting
logs fully RFC 5424 compatible what, in turn, allows to use syslog-ng or logstash for further processing.

#### Example:
    

```Text
<14>1 2017-01-16T16:25:50.742604Z hub.svale.netledger.com test.py 29293 MSGID148461275026504514 [default application="test.py" path="test.py:19" user="vagrant" levelname="ERROR" funcName="<module>" json_data="
{
        "object": "dumped",
        "some": "json",
        "by": "ops-logs"
}
"] here example log
```

## Features:

1. Useful attrs like user, application name, hostname, path/lineno, pid are automatically added to the log.
2. Standard interface
3. Concurrent safety. Multiple programs can write into single file, module watches for external changes.


## Interface:


#### Example:

```python
log.info('here test', repr=some_struct, jsonData=some_jsonable_struct, trace=1, stack=1, shorten=1000)
```

1. **repr** stands for putting pretty formatted multiline repr() of some_struct
2. **json_data** stands for dumping some_jsonable_struct into pretty formatted string inside log
3. **trace=1** makes sense when log is used inside except block, it automatically adds pretty formatted trace to the log data element and exception to the msg part.
4. **stack=1** adds callstack
5. **shorten=1000** limits amount of elements in passed to **json_data** or **repr** in order to pervent unintentional cpu consumption when logging huge objects. Default is 100. To disable set to 0.

    


## Tools:


**ngrep**: since local logs are multiline usual grep does bad job at looking though them. **ngrep** is available system wide after package installation. it finds substring which matches and returns full multiline record.
You can do like this

#### Example:

```bash
tail -f some.log | ngrep "string1|string2" | ngrep -v "string3|string4"
```

and interactively get relevant records. ngrep supports regex


## How to use:

Install it: `yum install ext_logging`

Configure your app:
        
```python
import ext_logging
ext_logging.configure_logs({
    'MODULES': {
        #configuring root - '' logger
        '': [
            {
                'handler': 'ext_logging.handlers.ConcurrentFileExtendedSysLogHandler',
                'filename': 'test.log',
                'json_serializer': YourCustomSerializerIfRequired,
                'level': 'INFO'
            }
        ]
    }
})
```

use:

```python
from logging import getLogger
log = getLogger(__name__)
log.error('here testing')
```

