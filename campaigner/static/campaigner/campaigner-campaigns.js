/***
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.

This code assumes that HTML5 web storage is available.
TODO - Don't allow the user to select more than 5 campaigns.  The back-end only returns results for up to 5 valid campaigns.
***/

function Campaigns(api_url, table_body_id, campaigns_variable_name) {
    /*** Object Prototype
    Manage a list of campaigns the user supports.  The user can select campaigns for which
    she wants to contact voters.
    ***/

    this.display = function() {
        /***
        Given the element Id of a table, populate the table with campaigns.  This method
        also assigns index numbers to each input element for use with the 'invert' method.

        TODO - Use angular.js instead.
        ***/
        var table = document.getElementById(this.table_body_id);
        table.innerHTML = "";   // Clear the previous items

        for (var index = 0; index < this.campaigns.length; index++) {
            var new_tr = document.createElement("tr");

            var new_td_name = document.createElement("td");
            var new_label = document.createElement("label");
            new_label.setAttribute("for", "box" + index);
            new_label.innerHTML = this.campaigns[index].name;
            new_td_name.appendChild(new_label);
            new_tr.appendChild(new_td_name);

            var new_input = document.createElement("input");
            new_input.setAttribute("id", "box" + index);
            new_input.setAttribute("type", "checkbox");
            new_input.setAttribute("onclick", this.campaigns_variable_name + ".invert(" + index + ")");
            if (this.campaigns[index].contact) {
                new_input.setAttribute("checked", "checked");
            }

            var new_td_contact = document.createElement("td");
            new_td_contact.appendChild(new_input);
            new_tr.appendChild(new_td_contact);
            table.appendChild(new_tr);
        }
        this.save();    // TODO - delete when "onunload" is reliable
    };

    this.getCampaigns = function() {
        /***
        Assign an array of campaign objects to the 'campaigns' attribute.  First, look
        for relevant campaigns in local storage.  If none are present, make an API call.
        ***/
        if (localStorage.campaigns) {
            console.log('Found campaigns in local storage.');
            this.campaigns = JSON.parse(localStorage.campaigns);
            this.display();
            return;
        }

        // Didn't find campaigns in local storage.  Make an API call.
        var request = new XMLHttpRequest();
        // http://stackoverflow.com/questions/133973/how-does-this-keyword-work-within-a-javascript-object-literal
        var that = this;
        request.onreadystatechange = function() {
            if (request.readyState == 4) {
                console.log('Response received for campaigns request.  Status code: ' + request.status);
                if (request.status == 200) {
                    // The 'objects' attribute of the server's JSON response is an array of compaign
                    // objects.  It looks like: [{"id": 1, "name": "Smith for President"}, {...}, ...].
                    that.campaigns = JSON.parse(request.responseText).objects;

                    // Add additional attributes to the server's response.
                    for (var index = 0; index < that.campaigns.length; index++) {
                        // By default, all the campaigns should be selected for contacting associated
                        // voters, as reflected by an added 'contact' attribute set to True.
                        that.campaigns[index].contact = true;
                    }
                    that.display();
                }
            }
        };
        request.open('GET', this.api_url, true);
        request.setRequestHeader('Accept', 'application/json');
        console.log('Requesting campaigns from the server.');
        request.send();
    };

    this.invert = function(index) {
        /***
        For the campaign with the given index in the attribute array 'campaigns',
        logically negate the value of the 'contact' attribute.
        ***/
        console.log('invert(' + index + ')');
        this.campaigns[index].contact = !this.campaigns[index].contact;
        this.save();    // TODO - delete when "onunload" is reliable
    };

    this.save = function() {
        /***
        Write the 'campaigns' array attribute to localStorage.  The containing
        html page should call this method on unload.
        ***/
        if (this.campaigns && this.campaigns.length) {  // Boolean([]) is true
            localStorage.campaigns = JSON.stringify(this.campaigns);
        }
    };

    this.update = function() {
        /*** Update the array of campaigns by making an API call. ***/
        localStorage.removeItem('campaigns');
        this.getCampaigns();
    };

    // Initialization
    this.api_url = api_url;
    this.table_body_id = table_body_id;
    this.campaigns_variable_name = campaigns_variable_name;
    this.getCampaigns(); // Populate a 'campaigns' array attribute
}
