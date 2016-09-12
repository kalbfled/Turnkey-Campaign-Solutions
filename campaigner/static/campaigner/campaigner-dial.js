/***
(C) David J. Kalbfleisch 2013

All rights reserved.  You are welcome to inspect this code for your education or to evaluate
the author's qualifications.  No other uses are permitted.

This code assumes that HTML5 web storage is available.
***/

function getCampaignIDs() {
    /***
    Return an array of IDs of campaigns for which the user wants to contact voters.  The
    campaigns should be stored in local storage as a stringified object with attributes
    including 'id' and 'contact'.  If the latter is true, add the former to the array of
    values to return.
    ***/
    var IDs = [];

    if (localStorage.campaigns) {
        // [{"id": 1, "name": "Smith for President", "contact":true}, {...}, ...]
        var campaigns = JSON.parse(localStorage.campaigns);
        for (var index = 0; index < campaigns.length; index++) {
            if (campaigns[index].contact) {
                // The user wants to contact voters for this campaign
                IDs.push(campaigns[index].id);
            }
        }
    }
    return IDs;
}

function Voters(voter_api_url, ir_api_url, remaining_element, name_element, location_element, phone_number_element, campaign_ids) {
    /*** Object Prototype
    Manage a list of voters the user has contacted or will contact.
    ***/

    this.display = function() {
        /*** Populate the user interface with information for the voter with the given index. ***/
        if (!this.voters) {
            console.log('No voters.');
            this.restoreDefaults();
            return;
        }
        if (!this.voters.length) {
            this.restoreDefaults();
            alert("There are no voters for the campaigns you selected.  Please alter your selection.");
            return;
        }
        if (this.current_index > this.voters.length) {
            console.log('Current index out of bounds.  Resetting to zero.');
            this.current_index = 0;
        }
        document.getElementById(this.remaining_element).innerHTML = this.voters.length;
        var voter_name = document.getElementById(this.name_element);
        voter_name.innerHTML = this.voters[this.current_index].first_name + ' ' + this.voters[this.current_index].last_name;
        if (this.voters[this.current_index].gender) {
            voter_name.innerHTML += ' (' + this.voters[this.current_index].gender + ')';
        }
        document.getElementById(this.location_element).innerHTML = this.voters[this.current_index].address.city + ', ' +
            this.voters[this.current_index].address.state;
            
        // Display an unflagged phone number for the current voter
        var phone_number = this.getPhoneNumber();
        if (phone_number) {
            document.getElementById(this.phone_number_element).innerHTML = "<a href='tel:" + phone_number + "'>" + phone_number + "</a>";
        } else {
            // If a valid phone number doesn't exist, voters are not being removed from
            // this.voters appropriately after the user flags a phone number.
            console.log('No valid phone number for voter at index ' + this.current_index + '.');
            document.getElementById(this.phone_number_element).innerHTML = "No valid phone number";
        }
    };

    this.drop = function() {
        /***
        Remove the current voter from the array.  If the current voter is the last in the array,
        move to the beginning of the array, if applicable.  If the voter is the only voter in
        the array, delete it, and get more voters.
        ***/
        if (this.voters.length == 1) {
            // Delete the last voter, and try to get more
            this.voters = undefined;
            localStorage.removeItem('voters');
            this.restoreDefaults();
            this.getVoters();
            return;
        }
        if (this.current_index == (this.voters.length - 1)) {
            // The index points to the last voter in the array
            this.voters.pop();
            this.current_index = 0;
        } else {
            // Remove a voter from somewhere in the middle
            this.voters.splice(this.current_index, 1);
        }
        this.save();    // TODO - delete when "onunload" is reliable
        this.display();
    };

    this.flag = function() {
        /*** Flag the phone number for the current voter. ***/
        if (!this.voters || !this.voters.length) {
            return; // Nothing to do
        }
        var voter = this.voters[this.current_index]; // The voter at the current index
        if (voter.active_number == 1) {
            voter.number1_flagged = true;
            this.flags.push({
                "resource_uri": voter.resource_uri,
                "phone_number1": "flagged",
            });
        } else if (voter.active_number == 2) {
            voter.number2_flagged = true;
            this.flags.push({
                "resource_uri": voter.resource_uri,
                "phone_number2": "flagged",
            });
        }
        if (!this.getPhoneNumber()) {
            this.drop();    // Calls this.next()
            return;
        }
        this.next();
    };

    this.getDropValue = function() {
        /***
        Return the value of the "drop" url GET parameter, if present, as a number (not string).
        http://stackoverflow.com/questions/5448545/how-to-retrieve-get-parameters-from-javascript
        ***/
        var drop_string = /drop=\d+/.exec(window.location.search);
        if (drop_string) {
            return Number(drop_string[0].slice(5));
        }
        return null;
    };

    this.getFlags = function() {
        /*** Load or create the 'flags' list, and return it. ***/
        if (localStorage.flags) {
            return JSON.parse(localStorage.flags);
        }
        return [];
    };

    this.getPhoneNumber = function() {
        /***
        For the voter at the current index, return a phone number not flagged, or return Null.
        If there is a phone number of length 10, convert it to xxx-xxx-xxxx format.
        ***/
        var phone_number = null;
        var voter = this.voters[this.current_index]; // The voter at the current index
        if (!voter.number1_flagged && voter.phone_number1) {
            voter.active_number = 1;
            phone_number = voter.phone_number1;
        } else if (!voter.number2_flagged && voter.phone_number2) {
            voter.active_number = 2;
            phone_number = voter.phone_number2;
        }
        if (phone_number && (phone_number.length == 10)) {
            phone_number = phone_number.slice(0,3) + "-" + phone_number.slice(3,6) + "-" + phone_number.slice(6);
        }
        return phone_number;
    };

    this.getVoters = function() {
        /***
        Assign an array of voter objects to the 'voters' attribute.  Make API calls as
        necessary.  API calls can include GET, to retrieve new voter data, and POST to
        submit intelligence reports (IRs).
        ***/
        this.current_index = 0;

        // First, look for recently downloaded voters in local storage
        if (localStorage.voters && this.lessThan48Hours()) {
            console.log('Found recent voters in local storage.');
            this.voters = JSON.parse(localStorage.voters);
            this.display();
            return;
        }

        if (localStorage.irs) {
            // Upload IR data before getting new voter contact information
            this.patchIRs();
        }

        // Upload data about flagged phone numbers before getting new voter contact information
        this.patchFlags();

        // Can't make a valid API call without campaign IDs
        if (!this.campaign_ids || !this.campaign_ids.length) {
            return;
        }
        
        // Didn't find unexpired, uncontacted, contactable voters in local storage.  Make API calls
        // as necessary.
        var request = new XMLHttpRequest();
        // http://stackoverflow.com/questions/133973/how-does-this-keyword-work-within-a-javascript-object-literal
        var that = this;
        request.onreadystatechange = function() {
            if (request.readyState == 4) {
                console.log('Response received for voters request.  Status code: ' + request.status);
                if (request.status == 200) {
                    // The 'objects' attribute of the server's JSON response is an array of voter
                    that.voters = JSON.parse(request.responseText).objects;

                    // Add additional attributes to the server's response.
                    for (var index = 0; index < that.voters.length; index++) {
                        that.voters[index].number1_flagged = false;
                        that.voters[index].number2_flagged = false;
                    }

                    localStorage.last_voters_download = new Date();  // Saves the current date-time as a string
                    that.save();    // TODO - delete when "onunload" is reliable
                    that.display();
                }
            }
        };
        request.open('GET', this.voter_api_url + '?campaign_id=' + this.campaign_ids, true);
        request.setRequestHeader('Accept', 'application/json');
        console.log('Requesting voters from the server.');
        request.send();
    };

    this.lessThan48Hours = function() {
        /*** Return True if voters where last requested from the server less than 48 hours ago. ***/
        if (localStorage.last_voters_download) {
            var last_download = new Date(localStorage.last_voters_download);
            return ((new Date() - last_download) < 172800000); // 48 hours in milliseconds
        }
        return false;
    };

    this.makeIR = function(ir_html_url) {
        /***
        Change location to the html page for making an IR.  Pass as a GET parameter the Id of the
        voter for which the user wants to submit an IR and the current index of the voter.
        ***/
        window.location = ir_html_url + '?id=' + this.voters[this.current_index].id +
            '&index=' + this.current_index;
    };

    this.next = function() {
        /*** Advance to the next voter in the queue. ***/
        if (!this.voters) {
            return; // Nothing to show
        }
        if (this.current_index == (this.voters.length - 1)) {
            // Go back to the start of the queue
            this.current_index = 0;
        } else {
            this.current_index++;
        }
        this.display();
    };

    this.patchFlags = function() {
        /***
        Asyncronously PATCH flags to the server.  A 202 response indicates that the server accepted the request
        but gives no additional information.  In this event, set this.flags to an empty list.
        ***/
        if (!this.flags || !this.flags.length) {
            return;
        }
        var request = new XMLHttpRequest();
        // http://stackoverflow.com/questions/133973/how-does-this-keyword-work-within-a-javascript-object-literal
        var that = this;
        request.onreadystatechange = function() {
            if (request.readyState == 4) {
                console.log('Response received for flags patch request.  Status code: ' + request.status);
                if (request.status == 202) {
                    that.flags = [];
                }
            }
        };
        request.open('PATCH', this.voter_api_url, true);
        request.setRequestHeader('Content-Type', 'application/json');
        console.log('PATCHing flags to the server.');
        request.send(JSON.stringify({"objects":this.flags}));
    };

    this.patchIRs = function() {
        /***
        Asyncronously PATCH IRs to the server.  A 202 response indicates that the server accepted the request
        but gives no additional information.  In this event, remove the IRs from local storage.
        
        This method assumes that IRs are present in local storage.
        ***/
        var request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (request.readyState == 4) {
                console.log('Response received for IRs patch request.  Status code: ' + request.status);
                if (request.status == 202) {
                    localStorage.removeItem('irs');
                }
            }
        };
        request.open('PATCH', this.ir_api_url, true);
        request.setRequestHeader('Content-Type', 'application/json');
        console.log('PATCHing IRs to the server.');
        request.send(localStorage.irs);
    };

    this.restoreDefaults = function() {
        document.getElementById(this.remaining_element).innerHTML = "0";
        document.getElementById(this.name_element).innerHTML = "Name: No data";
        document.getElementById(this.location_element).innerHTML = "Location: No data";
        document.getElementById(this.phone_number_element).innerHTML = "No phone number";
    };

    this.save = function() {
        /***
        Write this.voters and, if applicable, this.flags, to localStorage.  The containing html page
        should call this method on unload.
        ***/
        if (this.voters && this.voters.length) {  // Boolean([]) is true; don't save an empty array
            localStorage.voters = JSON.stringify(this.voters);
        }
        if (this.flags && this.flags.length) {  // Boolean([]) is true; don't save an empty array
            localStorage.flags = JSON.stringify(this.flags);
        }
    };

    // Initialization
    this.voter_api_url = voter_api_url;     // list GET
    this.ir_api_url = ir_api_url;           // list POST
    this.remaining_element = remaining_element;
    this.name_element = name_element;
    this.location_element = location_element;
    this.phone_number_element = phone_number_element;
    this.campaign_ids = campaign_ids;       // The currently selected campaigns
    this.getVoters();                       // Populate a 'voters' array attribute
    this.flags = this.getFlags();           // Populate a 'flags' array attribute

    // If returning from ir.html, set the current index to match the "drop" GET parameter, and drop that voter
    var drop_parameter = this.getDropValue();
    if (drop_parameter != null) {       // 0 is valid, but Boolean(0) is false
        this.current_index = drop_parameter;
        this.drop();
    }
}
