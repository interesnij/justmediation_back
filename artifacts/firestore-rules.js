rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Function: get current user id.
    function getUser() {
      return int(request.auth.uid);
    }

    // Function: check authentication.
    function isAuthenticated() {
      return request.auth.uid != null && request.auth.uid != "";
    }

		//	**********************************************************************************
		//  Chats related permissions
    match /chats/{chat_id} {

      // Function: check if user is Chat participant.
      function isChatParticipant() {
        return getUser() in resource.data.participants;
      }

      // Permissions: chat permissions rules.
      allow get, list, update, create, delete: if isAuthenticated() && isChatParticipant();

      match /messages/{document=**} {

      	// Function: get chat of the current message
        function getCurrentChat() {
          return get(/databases/$(database)/documents/chats/$(chat_id));
        }

        // Function: check if user is message related chat participant.
        function isCurrentChatParticipant() {
    	    return getUser() in getCurrentChat().data.participants;
        }

      	// Permissions: messages permissions rules.
      	allow get, list, update, create, delete: if isAuthenticated() && isCurrentChatParticipant();

      }
    }


    //	**********************************************************************************
		//  Users statistics related permissions
    match /users/{user_id} {

      // Function: check if current user tries to get his own statistics
      function isCurrentUserStatistics() {
        return getUser() == int(user_id);
      }

      // Function: check if current user tries to get statistics for chat where it's participant
      function isChatParticipant() {
        return getUser() == resource.data.another_participant_id || getUser() in resource.data.participants;
      }

      // Permissions: users permissions rules.
      allow get, list, update, create, delete: if isAuthenticated() && isCurrentUserStatistics();

      match /chats/{document=**} {

      	// Permissions: statistics chats permissions rules.
      	allow get, list, update, create, delete: if isAuthenticated() && (isCurrentUserStatistics() || isChatParticipant());

      }
    }
  }
}


////////////////////////////// а вот так было
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}