// Shortcut to check that client can get data from Firebase (Cloud Firestore)
// docs: https://firebase.google.com/docs/firestore/quickstart
// install npm
// npm install firebase
// node artifacts/web-firebase-snippet.js

const firebase = require("firebase");
require("firebase/firestore");
const firebaseConfig = require('../config/google-credentials/project-settings.json');
firebase.initializeApp(firebaseConfig);

// get firebase auth token from `/api/v1/firebase/get-credentials/`
let token = "";
firebase.auth().onAuthStateChanged(function(user) {
  if (user) {
    // User is signed in.
    console.log(`User (uid:${user.uid}) is signed in.`);

    // Users
    // get whole users collection
    let user_id = user.uid;
    let chat_id = 'enter_chat_id';
    getCollection(`users`);
    getDocument(`users/${user_id}/`);
    getCollection(`users/${user_id}/chats`);
    getDocument(`users/${user_id}/chats/${chat_id}`);

    // Chats
    // get whole chats collection
    chat_id = 'enter_chat_id';
    let message_id = 'enter_message_id';
    getCollection(`chats`);
    getDocument(`chats/${chat_id}/`);
    getCollection(`chats/${chat_id}/messages`);
    getDocument(`chats/${chat_id}/messages/${message_id}/`);
  } else {
    // User is signed out.
  }
});
firebase.auth().signInWithCustomToken(token).catch(function(error) {
  let errorCode = error.code;
  let errorMessage = error.message;
  console.log(`Auth error. Code: ${errorCode}. Message: ${errorMessage}.`)
});

let db = firebase.firestore();

// Simple function to get objects collection
function getCollection(path) {
  db.collection(path)
    .get()
    .then((querySnapshot) => {
      querySnapshot.forEach((doc) => {
        console.log(`${doc.id} => ${doc.data()
          }`);
      });
    }).catch(function(error) {
      let errorCode = error.code;
      let errorMessage = error.message;
      console.log(
        `Error getting collection. Path: ${path}. Code: ${errorCode}. Message: ${errorMessage}.`
      )
    });
}

// Simple function to get collection document
function getDocument(path) {
  db.doc(path)
    .get()
    .then((querySnapshot) => {
      console.log(`${querySnapshot.id} => ${querySnapshot.data()
        }`);
    }).catch(function(error) {
      let errorCode = error.code;
      let errorMessage = error.message;
      console.log(
        `Error getting document. Path: ${path}. Code: ${errorCode}. Message: ${errorMessage}.`
      )
    });
}
