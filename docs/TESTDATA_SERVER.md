# Testdata Server

Run testdata as a server so non-python codebases (like a Javascript frontend) can hook into the same testing data as the backend. All back and forth with the testdata server uses json.

The server can be started on the command line (Any port above 4000 can be used):

```
$ testdata serve --host=<HOST> --port=<PORT>
```

And a request to a specific testdata method can be done using a GET or POST request to the a url like:

```
<HOST>:<PORT>/<METHOD-NAME>?<METHOD-ARG-1>=<VALUE-1>&...
```

## Example

Start the server:

```
$ testdata serve --host=127.0.0.1 --port=13516
Server is listening on 127.0.0.1:13516
```

And request a 64 character ascii string:

```
$ curl http://127.0.0.1:13516/get_ascii?size=64
"7arPxqBKTtudL1ZHEoVF5fqLVkVTY78BTPCXsZ24BJf9m5C9yKMOgX7ooBS39wpY"
```

The method arguments can also be passed as json:

```
$ curl http://127.0.0.1:13516/get_name -H "Content-Type: application/json" -d '{"name_count": 1}'
"Demarcus"
```

If a testdata method returns an object, that object will be checked for a `jsonable`, `to_json`, or `json` method and the return value of that method will be returned as the body.