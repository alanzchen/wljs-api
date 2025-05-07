/* Polyfill for React based websites. It replaces server object and redirect all output to buffers */
/* add it to the head tag using any CDN */

//setting up global virtual server
const server = {};
window.server = server;

let promises;
let symbols;
let eventsPool;

server.loadObjects = (result) => {
    interpretate(result.objects, {hold:true}).then((i) => {
        console.warn('Objects loaded!');
        Object.keys(i).forEach((oName) => {
          const obj = new ObjectStorage(oName);
          obj.cache = i[oName];
          obj.cached = true;
        });

        Object.keys(promises).forEach((key) => {
          if (Array.isArray(promises[key])) {
            promises[key].forEach((el) => el.resolve(i[key]));
          } else {
            promises[key].resolve(i[key]);
          }
        })
      });

      interpretate(result.symbols, {hold:true}).then((i) => {
        console.warn('Symbols loaded!');
        Object.keys(i).forEach((oName) => {
          core[oName] = async (args, env) => {
            const data = await interpretate(core[oName].data, env);
            return data;
          }
          core[oName].data = i[oName]
          core[oName] = async (args, env) => {
            console.log('IE: calling our symbol...');
            //evaluate in the context
            const data = await interpretate(core[oName].data, env);
        
            if (env.root && !env.novirtual) core[oName].instances[env.root.uid] = env.root; //if it was evaluated insdide the container, then, add it to the tracking list
            //if (env.hold) return ['JSObject', core[name].data];
        
            return data;
          }
        
          core[oName].update = async (args, env) => {
            //evaluate in the context
            //console.log('IE: update was called...');
        
            //cache good for numerics
            if (env.useCache) {
              if (!core[oName].cached || core[oName].currentData != core[oName].data) {
                core[oName].cached = await interpretate(core[oName].data, env);
                core[oName].currentData = core[oName].data; //just copy the reference
                //console.log('cache miss');
              } 
        
              return core[oName].cached;
            }
        
            const data = await interpretate(core[oName].data, env);
            //if (env.hold) return ['JSObject', data];
            return data;
          }  
        
          core[oName].destroy = async (args, env) => {
        
            delete core[oName].instances[env.root.uid];
            console.warn(env.root.uid + ' was destroyed')
            console.warn('external symbol was destoryed');
          }  
        
          core[oName].data = structuredClone(i[oName]); //get the data
        
          core[oName].virtual = true;
          core[oName].instances = {};

        });

        Object.keys(symbols).forEach((key) => {
          console.warn(key);
          symbols[key].resolve(i[key]);
        });
      });
      
      
}

server.flushEvents = () => {
    eventsPool.forEach((ev) => {
        if (ev[0] == 'fire') {
          server.kernel.io.fire(ev[1], ev[2], ev[3]);
        } else if (ev[0] == 'poke') {
          server.kernel.io.poke(ev[1]);
        }
    });
    eventsPool = [];
}

server.resetIO = () => {
    console.warn('Virtual server hard reset');

    promises = {};
    symbols =  {};
    eventsPool = [];

    server.kernel = {
        io: {
          fire(uid, payload, pattern="Default") {
            eventsPool.push(['fire', uid, payload, pattern]);
          },
          poke(uid) {
            eventsPool.push(['poke', uid]);
          }
        }
    };

    server.io = {};

    server.ask = (what) => {
        const p = new Deferred();
        
        if (what.length < 42) {
          console.error('Unknown command');
          console.error(what);
          return false;
        }
        //throw what;
        const offset = 'CoffeeLiqueur`Extensions`FrontendObject`Internal`GetObject["'.length;
        if (Array.isArray(promises[what.slice(offset,-2)])) {
          promises[what.slice(offset,-2)].push(p);
        } else {
          promises[what.slice(offset,-2)] = [p];
        }
        
        return p.promise;
      }

      server.getSymbol = (name) => {
        const p = new Deferred();

        console.warn('Asking for symbol' + name);

        symbols[name] = p;
        return p.promise;
      }
}

var addr = 'http://127.0.0.1:20560';
var fetchOptions = {};
var polingDelay = 300;

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

server.configure = ({address = 'http://127.0.0.1:20560', fetchOptions = {}, polingDelay = 300}) => {
    addr = address;
    fetchOptions = fetchOptions;
    polingDelay = polingDelay;
}

server.waitForConnection = async () => {
    try {
      const res = await fetch(addr + '/api/ready/', { method: 'POST', ...fetchOptions });
      console.warn(res);
      const r = await res.json();
      if (!r.ReadyQ) {
        await delay(polingDelay);
        await checkConnection();
      }
    } catch (err) {
      await delay(polingDelay);
      await checkConnection();
    }
  };

server.findKernel = async () => {
    const res = await fetch(addr + '/api/kernels/list/', {
        method:'POST', ...fetchOptions
    });
    
    const body = await res.json();


    const valid = body.filter((el) => el.ContainerReadyQ);
    if (valid.length == 0) {
        await delay(polingDelay);
        return await findKernel();
    }

    return valid[0].Hash;
}

server.getResult = async (kernel, transaction) => {
    await delay(polingDelay);

    let result = await fetch(addr + '/api/transactions/get/', {
        method:'POST',
        body:JSON.stringify({
            'Hash': transaction
        }),
        ...fetchOptions
    });

    result = await result.json();
    console.log(result);

    if (!(result.State == 'Idle')) result = await getResult(kernel, transaction);

    
    return result.Result;

}

server.createTransaction = async (kernel, data) => {
    const trimmed = data.trim();
    if (trimmed.length == 0) return;

    let transaction = await fetch(addr + '/api/transactions/create/', {
                    method:'POST',
                    body:JSON.stringify({
                        'Kernel': kernel,
                        'Data': trimmed
                    }),
                    ...fetchOptions
    });

    transaction = await transaction.json();
    return transaction;
}

server.requestCDNExtensionsList = async () => {
    const listRes = await fetch(addr + '/api/cdn/list/', { method: 'POST', ...fetchOptions });
    return await listRes.json();
}

server.requestCDNJavascript = async (list) => {
    const listRes = await fetch(addr + '/api/cdn/get/js/', { method: 'POST', body:JSON.stringify(list), ...fetchOptions });
    return await listRes.json();
}

server.requestCDNStyles = async () => {
    const listRes = await fetch(addr + '/api/cdn/get/styles/', { method: 'POST', ...fetchOptions });
    return await listRes.json();
}

server.requestObject = async (kernel, uid) => {
    let r = await fetch(addr + '/api/frontendobjects/get/', {
        method:'POST',
        body:JSON.stringify({
          'UId': uid,
          'Kernel': kernel
        }),
        ...fetchOptions
    });

    r = await r.json();

    if (r.Resolved == true) {
        return JSON.parse(r.Data);
    }

    await delay(polingDelay);

    return await requestObject(kernel, uid)
}

server.cachingFunction = async (objectId) => {
    const res = await server.requestObject(null, objectId);
    return res;
}

//implemetation of get method depends on execution env
window.ObjectStorage.prototype.get = function () {
      if (this.cached) return this.cache;
      const self = this;
      const promise = new Deferred();

      server.cachingFunction(self.uid).then((result) => {
        if (!result) {
            console.warn('Rejected! Not found');
            promise.reject();
            return;
        }
        self.cache = result;
        promise.resolve(self.cache);
      })
  
      return promise.promise;
    }



//Polyfills fro WLJSIO package
core.Offload = (args, env) => {
    if (args.length > 1) {
        //alternative path - checking options
        //do it in ugly superfast way
        if (args[1][1] === "'Static'") {
            if (args[1][2]) {
                return interpretate(args[0], {...env, static: true});
            }
        } else if (args.length > 2) {
            if (args[2][1] === "'Static'") {
                if (args[2][2]) {
                    return interpretate(args[0], {...env, static: true});
                }                
            }
        }
    }
  
    return interpretate(args[0], env);
  }

  core.Medium = () => 0.7
  
  core.Offload.update = (args, env) => {
    if (args.length > 1) {
        //alternative path - checking options
        //do it in ugly superfast way
  
        //Volitile -> False -> Reject updates
  
        //low-level optimizations, we dont' need to spend time on parsing options
        if (args[1][1] === "'Volatile'") {
            if (!args[1][2]) {
                console.log('Update was rejected (Nonvolatile)');
                return;
            }
        } else if (args.length > 2) {
            if (args[2][1] === "'Volatile'") {
                if (!args[2][2]) {
                    console.log('Update was rejected (Nonvolatile)');
                    return;
                }                
            }
        }
    }
  
    return interpretate(args[0], env);
  }
