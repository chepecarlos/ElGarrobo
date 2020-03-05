var OBSWebSocket = require('obs-websocket-js');

// npm install node-telegram-bot-api

console.log(process.argv[2]);

const obs = new OBSWebSocket();
obs.connect({
  address: 'Ryuk.local:4444'
}).then(() => {
  console.log(`Conectado`);
  if (process.argv[2] == "esena") {
    console.log("Cambiar Esena")
    obs.send('SetCurrentScene', {
      'scene-name': process.argv[3]
    });
  } else if (process.argv[2] == "striming") {
    console.log("Cambiar Estado Striming")
    if (process.argv[3] == "empezar") {
      obs.sendCallback('StartStreaming', (error) => {
        console.log(error);
        // Code here...
      });
    } else if (process.argv[3] == "parar") {
      obs.sendCallback('StopStreaming', (error) => {
        console.log(error);
        // Code here...
      });
    }
  } else if (process.argv[2] == "grabar") {
    console.log("Cambiar Estado Grabacion")
    if (process.argv[3] == "empezar") {
      obs.sendCallback('StartRecording', (error) => {
        console.log(error);
        // Code here...
      });
    } else if (process.argv[3] == "parar") {
      obs.sendCallback('StopRecording', (error) => {
        console.log(error);
        // Code here...
      });
    }
  } else if (process.argv[2] == "mute") {
    console.log("Cambiando mute");
    obs.send('ToggleMute', {
      'source': process.argv[3]
    });
  } else if (process.argv[2] == "Verde") {
    console.log("Cambiar pantalla verde");
    if (process.argv[3] == "Encender") {
      obs.sendCallback('SetSourceFilterVisibility', {
        'sourceName': 'CamaraHDMI',
        'filterName': 'FondoVerde',
        'filterEnabled': true
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    } else if (process.argv[3] == "Apagar") {
      obs.sendCallback('SetSourceFilterVisibility', {
        'sourceName': 'CamaraHDMI',
        'filterName': 'FondoVerde',
        'filterEnabled': false
      }, (error, data) => {
        if (error) {
          console.log(error);
        }
        console.log(data)
      });
    }
    // obs.sendCallback('GetSourceSettings',{
    //   'sourceName' : 'CamaraHDMI'
    // } ,(error, data) => {
    //   if (error) {
    //     console.log(error);
    //   }
    //   console.log(data)
    // });

    // obs.sendCallback('GetSourceFilters', {
    //   'sourceName': 'CamaraHDMI'
    // }, (error, data) => {
    //   if (error) {
    //     console.log(error);
    //   }
    //   console.log(data)
    // });


  }

  obs.disconnect();
}).catch(err => {
  console.log(err);
});

obs.on('SwitchScenes', data => {
  console.log(`New Active Scene: ${data.sceneName}`);
});

obs.on('GetSourceFilters', (data) => {
  console.log(data);
});

obs.on('error', err => {
  console.error('socket error:', err);
});
