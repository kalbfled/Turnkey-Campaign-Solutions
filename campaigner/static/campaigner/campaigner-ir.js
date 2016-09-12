/***
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.

This code assumes that HTML5 web storage is available.
***/

function Issues(api_url, issues_list) {
    /*** Object Prototype
    Populate a list of issues objects, and make this list options in drop-down boxes on ir.html.
    ***/

    this.addIssue = function() {
        /***
        Add a new issue row.  Don't add new text directly to the innerHTML attribute of the issues list
        element because it creates undesirable results when the browser automatically closes tags.
        ***/
        var new_select = document.createElement("select");
        for (var i=0; i<this.issues.length; i++) {
            var new_option = document.createElement("option");
            new_option.setAttribute("value", this.issues[i].id);
            new_option.innerHTML = this.issues[i].issue;
            new_select.appendChild(new_option);
        }

        var new_label_support = document.createElement("label");
        new_label_support.setAttribute("for", "support" + this.issues_counter);
        new_label_support.innerHTML = "Support";

        var new_input_support = document.createElement("input");
        new_input_support.setAttribute("type", "radio");
        new_input_support.setAttribute("name", "pref" + this.issues_counter);
        new_input_support.setAttribute("id", "support" + this.issues_counter);
        new_input_support.setAttribute("value", "support");

        var new_label_oppose = document.createElement("label");
        new_label_oppose.setAttribute("for", "oppose" + this.issues_counter);
        new_label_oppose.innerHTML = "Oppose";

        var new_input_oppose = document.createElement("input");
        new_input_oppose.setAttribute("type", "radio");
        new_input_oppose.setAttribute("name", "pref" + this.issues_counter);
        new_input_oppose.setAttribute("id", "oppose" + this.issues_counter);
        new_input_oppose.setAttribute("value", "oppose");

        // Create a button to remove the issue (li element)
        var new_span = document.createElement("span");
        new_span.setAttribute("class", "glyphicon glyphicon-remove-sign");
        var new_button = document.createElement("button");
        new_button.setAttribute("class", "btn btn-default btn-sm");
        new_button.setAttribute("style", "margin-left: 3px;");
        new_button.setAttribute("onclick", "removeIssue(" + this.issues_counter + ");");
        new_button.appendChild(new_span);

        var new_li = document.createElement("li");
        new_li.setAttribute("id", "issue" + this.issues_counter);
        new_li.setAttribute("class", "list-group-item");
        new_li.appendChild(new_select);
        new_li.appendChild(new_button);
        new_li.appendChild(document.createElement("br"));
        new_li.appendChild(new_label_support);
        new_li.appendChild(new_input_support);
        new_li.appendChild(new_label_oppose);
        new_li.appendChild(new_input_oppose);

        document.getElementById(this.issues_list).appendChild(new_li);
        this.issues_counter++;
    };

    this.getIssues = function() {
        /***
        If local storage contains issues, and if the last syncronization with the server is less than 30 days ago,
        use the issues in local storage.  Otherwise, make an API call.  The server returns issues in alphabetical
        order.
        ***/
        if (localStorage.issues && this.lessThan30Days()) {
            console.log('Found recent issues in local storage.');
            this.issues = JSON.parse(localStorage.issues);
            this.addIssue();
            return;
        }
        
        // Didn't find unexpired issues in local storage.  Make an API call.
        var request = new XMLHttpRequest();
        // http://stackoverflow.com/questions/133973/how-does-this-keyword-work-within-a-javascript-object-literal
        var that = this;
        request.onreadystatechange = function() {
            if (request.readyState == 4) {
                console.log('Response received for issues request.  Status code: ' + request.status);
                if (request.status == 200) {
                    // The 'objects' attribute of the server's JSON response is an array of issues
                    // [{"id": 2, "issue": "direct election of President"}, ...]
                    that.issues = JSON.parse(request.responseText).objects;
                    localStorage.issues = JSON.stringify(that.issues);
                    localStorage.last_issues_download = new Date(); // Saves the current date-time as a string
                    that.addIssue();
                }
            }
        };
        request.open('GET', this.api_url, true);
        request.setRequestHeader('Accept', 'application/json');
        console.log('Requesting issues from the server.');
        request.send();
    };

    this.getPreferences = function() {
        /***
        Return an object of the form {"support":[issue_id1, issue_id2, ...], "oppose":[issue_id3, ...]}.
        This method assumes that all "select" and "input" elements in the containing html page relate
        to issue preferences.  Ignore duplicate issues (even if support/oppose differs).
        ***/
        var select_elements = document.getElementsByTagName('select');
        var input_elements = document.getElementsByTagName('input');    // Should be all radio inputs
        var preferences = {"support":[], "oppose":[]};
        for (var i=0; i<select_elements.length; i++) {
            // Ignore duplicate issues (issues already in the "support" or "oppose" list)
            if ((preferences.support.indexOf(select_elements[i].value) == -1) &&
                    (preferences.oppose.indexOf(select_elements[i].value) == -1)) {
                if (input_elements[i*2].checked) {                      // Support
                    preferences.support.push(select_elements[i].value)
                } else if (input_elements[i*2 + 1].checked) {           // Oppose
                    preferences.oppose.push(select_elements[i].value)
                }
            }
        }
        // Don't include empty lists
        if (!preferences.support.length) {
            delete preferences.support;
        }
        if (!preferences.oppose.length) {
            delete preferences.oppose;
        }
        text = document.getElementById('additional').value;
        if (text) {
            preferences.text = text;
        }
        return preferences;
    };

    this.lessThan30Days = function() {
        /*** Return True if voters where last requested from the server less than 30 days ago. ***/
        if (localStorage.last_issues_download) {
            var last_download = new Date(localStorage.last_issues_download);
            return ((new Date() - last_download) < 2592000000); // 30 days in milliseconds
        }
        return false;
    };

    // Initialization
    this.api_url = api_url;
    this.issues_list = issues_list;
    // The number of issues on which the user is reporting for the given voter.  This is not decremented
    // when an issue is removed, but that doesn't matter.  Things work as long as no input element Id
    // is duplicated.
    this.issues_counter = 0;
    this.getIssues();
}

function IR(dial_url, voter_name) {
    /*** Object Prototype
    Manage the user's submission of an intelligence report (IR) for a specific voter.
    ***/

    this.getVoterId = function() {
        /***
        Return the value of the "id" url GET parameter.
        http://stackoverflow.com/questions/5448545/how-to-retrieve-get-parameters-from-javascript
        ***/
        var id_string = /id=\d+/.exec(window.location.search);
        if (id_string) {
            return id_string[0].slice(3);   // Return the digit portion of the string
        }
        return null;
    };

    this.getVoterIndex = function() {
        /***
        Return the value of the "index" url GET parameter.
        http://stackoverflow.com/questions/5448545/how-to-retrieve-get-parameters-from-javascript
        ***/
        var index_string = /index=\d+/.exec(window.location.search);
        if (index_string) {
            return index_string[0].slice(6);   // Return the digit portion of the string
        }
        return null;
    };

    this.submit = function(issue_prefs) {
        /***Record the user's submission, and return to dial.html.***/
        if (!(issue_prefs.support || issue_prefs.oppose || issue_prefs.text)) {
            // At least one of 'support', 'oppose', and 'text' must be non-empty
            alert("Please provide useful information to your campaigns.");
            return;
        }
        var irs;
        if (localStorage.irs) {
            irs = JSON.parse(localStorage.irs);
        } else {
            // The attribute "objects" is consistent with the Tastypie implementation for PATCH requests
            irs = {"objects":[]};
        }
        irs.objects.push({
            "method": 1,                 // Telephone (voice)
            "voter": this.voter_id,
            "intelligence_report": issue_prefs,
        });
        localStorage.irs = JSON.stringify(irs);
        window.location = dial_url + '?drop=' + this.voter_index;
    };

    // Initialization
    this.voter_id = this.getVoterId();
    this.voter_index = this.getVoterIndex();
    if (!this.voter_id || !this.voter_index) {
        // A required parameter is missing
        window.location = dial_url;
    } else {
        // Display the voter's name
        voters = JSON.parse(localStorage.voters);
        document.getElementById(voter_name).innerHTML = voters[this.voter_index].first_name + " " +
            voters[this.voter_index].last_name;
    }
}

function removeIssue(issue_id) {
    // TODO - Can I make this a method of Issues?
    var issue = document.getElementById("issue" + issue_id);
    document.getElementById("issues").removeChild(issue);
}
