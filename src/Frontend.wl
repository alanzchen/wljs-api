BeginPackage["CoffeeLiqueur`Extensions`API`", {
    "JerryI`Misc`Async`",
    "JerryI`Misc`Events`",
    "CoffeeLiqueur`Notebook`Transactions`",
    "JerryI`Misc`Events`Promise`",
    "JerryI`Misc`WLJS`Transport`",
    "JerryI`WLX`Importer`",
    "KirillBelov`HTTPHandler`",
    "KirillBelov`HTTPHandler`Extensions`",
    "KirillBelov`Internal`",
    "CoffeeLiqueur`Extensions`FrontendObject`"
}]


Begin["`Internal`"]

Needs["CoffeeLiqueur`ExtensionManager`" -> "WLJSPackages`"];

Needs["CoffeeLiqueur`Notebook`Cells`" -> "cell`"];
Needs["CoffeeLiqueur`Notebook`" -> "nb`"];

Needs["CoffeeLiqueur`Notebook`Kernel`" -> "GenericKernel`"];
Needs["CoffeeLiqueur`Notebook`Evaluator`" -> "StandardEvaluator`"];
Needs["CoffeeLiqueur`Notebook`AppExtensions`" -> "AppExtensions`"];


apiCall[request_] := With[{type = request["Path"]},
    Echo["API Request >> "<>type];
    With[{r = ExportByteArray[apiCall[request, type], "JSON"]},
        <|
            "Body" -> r, 
            "Code" -> 200, 
            "Headers" -> <|
                "Content-Length" -> Length[r], 
                "Connection"-> "Keep-Alive", 
                "Keep-Alive" -> "timeout=5, max=1000", 
                "Access-Control-Allow-Origin" -> "*"
            |>
        |>
    ]
]

apiCall[_, _] := "Undefined API pattern"

apiCall[request_, "/api/"] := {
    "/api/kernels/",
    "/api/transactions/",
    "/api/frontendobjects/",
    "/api/extensions/",
    "/api/ready/"
}

apiCall[request_, "/api/ready/"] := <|"ReadyQ" -> True|>


apiCall[request_, "/api/frontendobjects/"] := {
    "/api/frontendobjects/get/"
}


objects = <||>;

apiCall[request_, "/api/frontendobjects/get/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{
        k = If[StringQ[body["Kernel"] ], 
            SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Kernel"]) &],  
            SelectFirst[AppExtensions`KernelList, (TrueQ[#["ContainerReadyQ"] ] && TrueQ[#["ReadyQ"] ]) &]
        ],
        uid = body["UId"],
        promise = Promise[]
    },
        If[!KeyExistsQ[objects, uid],
            If[MissingQ[k], $Failed, 
                With[{
                    promiseId = promise // First
                },
                    GenericKernel`Async[k, With[{o = CoffeeLiqueur`Extensions`FrontendObject`Internal`GetObject[uid]},
                            EventFire[Internal`Kernel`Stdout[promiseId], Resolve, ExportString[o, "ExpressionJSON", "Compact"->1] ];
                        ]
                    ];
                ];

                objects[uid] = <|"Resolved" -> False|>;

                Then[promise, Function[data,
                    objects[uid] = Join[objects[uid], <|"Resolved" -> True,
                                                        "Data" -> data|>
                    ];
                ] ];

                objects[uid]

            ]
        ,
            objects[uid]
        ]
    ]    
]


apiCall[request_, "/api/transactions/"] := {
    "/api/transactions/create/",
    "/api/transactions/get/",
    "/api/transactions/delete/",
    "/api/transactions/list/"
}

transactions = {};

apiCall[request_, "/api/transactions/create/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{
        k = SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Kernel"]) &]
    },
        If[MissingQ[k], $Failed, 
            submitTransaction[body["Data"], k]
        ]
    ]
]

apiCall[request_, "/api/transactions/delete/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{
        m = SelectFirst[transactions, (#["Hash"] === body["Hash"]) &]
    },
        If[MissingQ[m], $Failed,
            transactions = transactions /. {m -> Nothing};
            True
        ]
    ]
]

apiCall[request_, "/api/transactions/get/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{
        m = SelectFirst[transactions, (#["Hash"] === body["Hash"]) &]
    },
        If[MissingQ[m], $Failed,
            <|
                "Hash" -> #["Hash"],
                "State" -> If[StringQ[#["State"] ], #["State"], "Undefined" ],
                "Result" -> If[ListQ[#["Result"] ], #["Result"], {} ]
            |>&@m
        ]
    ]
]

apiCall[request_, "/api/transactions/list/"] := With[{},
    With[{
        
    },
            <|
                "Hash" -> #["Hash"],
                "State" -> If[StringQ[#["State"] ], #["State"], "Undefined" ]
            |>& /@ transactions
    ]
]

submitTransaction[input_String, kernel_] := With[{transaction = Transaction[]},
   transactions = Append[transactions, transaction];
   transaction["Data"] = input;
   transaction["State"] = "Evaluation";
   transaction["Result"] = {};   
   transaction["EvaluationContext"] = <||>;

   EventHandler[transaction, {"Result" -> Function[data,
       (* AFTER, BEFORE, TYPE, PROPS can be altered using provided meta-data from the transaction *)

       If[data["Data"] != "Null",
           If[KeyExistsQ[data, "Meta"],
               transaction["Result"] = Append[transaction["Result"], <|"Data"->data["Data"], data["Meta"], "Type"->"Output"(*"" data["Meta"]*)|> ]
               
           ,
               transaction["Result"] = Append[transaction["Result"], <|"Data"->data["Data"], "Display"->"codemirror", "Type"->"Output"(*"" data["Meta"]*)|> ]
               
           ]
       ];
   ],
       "Finished" -> Function[Null,
           transaction["State"] = "Idle";
           Echo["Finished!"];
       ],

       "Error" -> Function[error,
           transaction["State"] = "Error";
           Echo["Error in evalaution... check syntax"];
       ]
   }];

   (* submit *)
   kernel["Container"][transaction];   
   transaction["Hash"]
]



apiCall[request_, "/api/kernels/"] := {
    "/api/kernels/list/",
    "/api/kernels/restart/",
    "/api/kernels/abort/",
    "/api/kernels/get/",
    "/api/kernels/create/",
    "/api/kernels/unlink/",
    "/api/kernels/init/",
    "/api/kernels/deinit/"
}

apiCall[request_, "/api/kernels/list/"] := With[{},
    <|
        "Hash"->#["Hash"], 
        "State"->#["State"], 
        "ReadyQ"->#["ReadyQ"], 
        "Name"->#["Name"],
        "ContainerReadyQ" -> TrueQ[#["ContainerReadyQ"] ]
    |> &/@ AppExtensions`KernelList
];

apiCall[request_, "/api/kernels/get/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{m = SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Hash"]) &]},
        If[MissingQ[m], $Failed,
            <|
                "Hash"->#["Hash"], 
                "State"->#["State"], 
                "ReadyQ"->#["ReadyQ"], 
                "Name"->#["Name"],
                "ContainerReadyQ" -> TrueQ[#["ContainerReadyQ"] ]
            |> & @ m
        ]
    ]
];

apiCall[request_, "/api/kernels/restart/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{m = SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Hash"]) &]},
        If[MissingQ[m], $Failed,
            GenericKernel`Restart[m];
            True
        ]
    ]
];

apiCall[request_, "/api/kernels/create/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    "Not implemented"
];

apiCall[request_, "/api/kernels/unlink/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    "Not implemented"
];

apiCall[request_, "/api/kernels/abort/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{m = SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Hash"]) &]},
        If[MissingQ[m], $Failed,
            GenericKernel`AbortEvaluation[m];
            True
        ]
    ]
];

apiCall[request_, "/api/kernels/init/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{m = SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Hash"]) &]},
        If[MissingQ[m], $Failed,
            initKernel[<|"env" -> $Env|>][m];
            True
        ]
    ]
];

apiCall[request_, "/api/kernels/deinit/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    With[{m = SelectFirst[AppExtensions`KernelList, (#["Hash"] === body["Hash"]) &]},
        If[MissingQ[m], $Failed,
            deinitKernel[m];
            True
        ]
    ]
];

{deinitKernel, initKernel}           = ImportComponent["Frontend/KernelUtils.wl"];

apiCall[request_, "/api/cdn/"] := {
    "/api/cdn/list/",
    "/api/cdn/get/js/",
    "/api/cdn/get/styles/"
}

apiCall[request_, "/api/cdn/get/js/"] := With[{
    body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"],
    thisrepo = WLJSPackages`Packages["wljs-api", "key"]
},
    Join[{
        "https://cdn.skypack.dev/twind/shim"
    }, getCDNJS[Flatten[{body}] /. {"common-css" -> Nothing}], {
        StringJoin[StringTemplate["https://cdn.jsdelivr.net/gh/``@``/"][getRepo[thisrepo ], getBranch[thisrepo ] ], "assets/polyfill.js" ]
    }]
]

apiCall[request_, "/api/cdn/get/styles/"] := With[{
    thisrepo = WLJSPackages`Packages["wljs-api", "key"]
},
    {
        StringJoin[StringTemplate["https://cdn.jsdelivr.net/gh/``@``/"][getRepo[thisrepo ], getBranch[thisrepo ] ], "assets/minimal.css" ]
    }
]

apiCall[request_, "/api/cdn/list/"] := With[{},
    Join[Map[Function[key, 
        key
    ], 
        Select[WLJSPackages`Packages // Keys, (WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], "minjs"]) &] 
    ] ]
]


getCDNJS[list_] := With[{}, 
  (With[{
    url = StringJoin[StringTemplate["https://cdn.jsdelivr.net/gh/``@``/"][getRepo[#["key"] ], getBranch[#["key"] ] ], #["path"] ]
  },

    url

  ]& /@ Flatten[Table[
      Table[
          <|"key"->WLJSPackages`Packages[i, "key"], "path"->j|>
      , {j, {WLJSPackages`Packages[i, "wljs-meta", "js"]} // Flatten}]
  , {i, list} ] ]) 
]

existsOrEmpty[settings_, field_] := If[KeyExistsQ[settings, field], settings[field], {}]

existsOrTrue[settings_, field_] := If[KeyExistsQ[settings, field], settings[field], True]


getRepo[Rule[_, url_String]] := StringReplace[url, "https://github.com/"~~s_:>s]
getBranch[Rule[_, url_String]] := "master"

getRepo[Rule[_, Rule[url_String, _]]] := StringReplace[url, "https://github.com/"~~s_:>s]
getBranch[Rule[_, Rule[url_String, branch_String]]] := branch


apiCall[request_, "/api/extensions/"] := {
    "/api/extensions/list/",
    "/api/extensions/get/minjs/",
    "/api/extensions/bundle/minjs/",
    "/api/extensions/get/styles/",
    "/api/extensions/bundle/styles/"
}

apiCall[request_, "/api/extensions/list/"] := With[{},
    Join[Map[Function[key, 
        <|"name" -> key, "version" -> WLJSPackages`Packages[key, "version"]|>
    ], 
        Select[WLJSPackages`Packages // Keys, (WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], "minjs"]) &] 
    ], {<|"name" -> "common-css", "version" -> "0.1"|>}]
]

pmIncludes[param_, whitelist_List] := 
Table[ 
    Table[ 
      Import[FileNameJoin[{"wljs_packages", WLJSPackages`Packages[i, "name"], StringSplit[j, "/"]} // Flatten], "Text"] // URLEncode
    , {j, {WLJSPackages`Packages[i, "wljs-meta", param]} // Flatten} ]
, {i, Select[WLJSPackages`Packages // Keys, (MemberQ[whitelist, #] && WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], param])&]}] // Flatten;

pmIncludesNoEncode[param_, whitelist_List] := 
Table[ 
    Table[ 
      Import[FileNameJoin[{"wljs_packages", WLJSPackages`Packages[i, "name"], StringSplit[j, "/"]} // Flatten], "Text"] 
    , {j, {WLJSPackages`Packages[i, "wljs-meta", param]} // Flatten} ]
, {i, Select[WLJSPackages`Packages // Keys, (MemberQ[whitelist, #] && WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], param])&]}] // Flatten;

pmIncludesNoEncode[param_, alterparam_, whitelist_List] := 
Table[ 
    Table[ 
      Import[FileNameJoin[{"wljs_packages", WLJSPackages`Packages[i, "name"], StringSplit[j, "/"]} // Flatten], "Text"] 
    , {j, {WLJSPackages`Packages[i, "wljs-meta", alterparam]} // Flatten} ]
, {i, Select[WLJSPackages`Packages // Keys, (MemberQ[whitelist, #] && WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], param])&]}] // Flatten;


apiCall[request_, "/api/extensions/get/minjs/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    pmIncludes["minjs", Flatten[{body}] /. {"common-css" -> Nothing} ]
]

inBlackList[key_] := MemberQ[{"wljs-markdown-support", "wljs-plotly", "wljs-wxf-accelerator", "wljs-html-support", "wljs-js-support", "wljs-sharedlib-mk", "wljs-mermaid-support", "wljs-revealjs"}, key]

globalWindow = ""

apiCall[request_, "/api/extensions/bundle/minjs/"] := With[{list = Select[WLJSPackages`Packages // Keys, (WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], "minjs"] && !inBlackList[#]) &] },
    StringJoin[globalWindow, "/* wljs-api bundler */\r\n{\r\n", StringRiffle[pmIncludesNoEncode["minjs", Flatten[{list}] ], "\r\n}\r\n{\r\n"], "\r\n}"] // URLEncode
]

common = Import[FileNameJoin[{$InputFileName // DirectoryName // ParentDirectory, "assets", "common.css"}], "Text"];

apiCall[request_, "/api/extensions/get/styles/"] := With[{body = ImportString[ByteArrayToString[request["Body"] ], "RawJSON"]},
    If[MemberQ[ Flatten[{body}], "common-css"], 
        Join[pmIncludes["styles", Flatten[{body}] ], {
            common // URLEncode
        }]
    ,
        pmIncludes["styles", Flatten[{body}] ]
    ]
]

apiCall[request_, "/api/extensions/bundle/styles/"] := With[{list = Select[WLJSPackages`Packages // Keys, (WLJSPackages`Packages[#, "enabled"] && KeyExistsQ[WLJSPackages`Packages[#, "wljs-meta"], "minjs"]) &]},
    StringRiffle[Join[pmIncludesNoEncode["styles", Flatten[{list}] ], {common}], "\r\n\r\n"] // URLEncode
]




With[{http = AppExtensions`HTTPHandler},
    http["MessageHandler", "ExternalAPI"] = AssocMatchQ[<|"Path" -> ("/api/"~~___)|>] -> apiCall;
];

End[]
EndPackage[]

