//Let's Get Personal

function loadDoc(url, func) {
    let xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            func(xhttp.response);
        }
    }
    xhttp.open("GET", url);
    xhttp.send();
}


//login.html
function login(){
    window.location.replace("/");
}

function Login() {
    let txtEmail = document.getElementById("txtEmail");
    let txtPassword = document.getElementById("txtPassword");

    if (txtEmail.value == '' || txtPassword.value == '') {
        alert("Email and password can not be blank.");
        return;
    }

    let URL = "/login?email=" + txtEmail.value + "&password=" + txtPassword.value;

    loadDoc(URL, login_response);
}

function login_response(response) {
    let data = JSON.parse(response);
    let result = data["result"];
    if (result != "OK") {
        alert(result);
    }
    else {
        window.location.replace("/feed.html");
    }

}
// forget the password
function forget(){
    window.location.replace("/forget.html");
}
function get(){
    let txtEmail = document.getElementById("txtEmail");
    if (txtEmail.value == ''){
        alert("Why you left it blank?");
        return;
    }
     let URL = "/get?email=" + txtEmail.value;
      loadDoc(URL, get_response);

}
function get_response(response) {
    let data = JSON.parse(response);
    if (data.password) {
        alert("Your password is: " + data.password);
    } else {
        alert(data.result);
    }
}
//signin.html
function signin(){
    window.location.replace("/signin.html");
}

function Signin(){
    let txtEmail = document.getElementById("txtEmail");
    let txtPassword = document.getElementById("txtPassword");
    let txtUsername = document.getElementById("txtUsername");

    let URL = "/signin?email=" + txtEmail.value + "&password=" + txtPassword.value + "&username=" + txtUsername.value;
    loadDoc(URL, signin_response);
}

function signin_response(response) {
    let data = JSON.parse(response);
    let result = data["result"];
    if (result != "OK") {
        alert(result);
    }
    else{
        window.location.replace("/feed.html");
    }

}


//profile.html
function profile(){
     loadDoc('/profile', profile_response)
}

function profile_response(response) {
    let users = JSON.parse(response).users;
    let divUsers = document.getElementById("divUsers");

    let content = '';
    for (let i = 0; i < users.length; i++) {
        let user = users[i];
        content += `<div><a href="/user_blogs/${user.email}">@${user.username}</a></div>`;
    }
    divUsers.innerHTML = content;
}


//user_blogs.html
function delete_blog(blogID) {
    loadDoc('/delete_blog/' + blogID, function(response) {
        location.reload();
    });
}

function add_blog(){
    let title = document.getElementById("title");
    let text = document.getElementById("text");

    let URL = "/add_blog?title=" + title.value + "&text=" + text.value;
    loadDoc(URL, editblog_response);
}

function editblog_response(response) {
    let data = JSON.parse(response);
    let result = data["result"];
    if (result != "OK") {
        alert(result);
    }
    else {
        location.reload();
    }

}


//add blog
function add(){
    let title = document.getElementById("title");
    let text = document.getElementById("text");

    let URL = "/add_blog?title=" + title.value + "&text=" + text.value;
    loadDoc(URL, editblog_response);
}



/*
function back(){
    window.location.replace("/account.html");
}

function list_blogs() {
    loadDoc('/list_blogs', list_blogs_response)
}
function list_blogs_response(response) {
    let blogs = JSON.parse(response);
    let divBlogs = document.getElementById("divBlogs");

    let content = "";
    for (let i = 0; i < blogs.length; i++) {
        let blog = blogs[i];
         content += '<div>' +
                       '<center>' +
                       '<h2>Title: ' + blog["title"] + '</h2>' +
                       '<p>' + blog["text"] + '</p>' +
                       '<p>Posted on: ' + blog["date"] + '</p>' +
                       '<a href="/delete_blog/' + blog['blogID'] + '" onclick="return confirm(\'Are you sure you want to delete this blog?\');">🗑️</a>' +
                       '</center>' +
                   '</div><br><br><br>';
    }
    divBlogs.innerHTML = content;
}
*/






/*
//Apartments search
function apartment_search() {
    let txtSearch = document.getElementById("txtSearch").value;
    let bedrooms = document.getElementById("bedrooms").value;
    let sort = document.getElementById("sort").value;

    let url = `/search?query=${txtSearch}&bedrooms=${bedrooms}&sort=${sort}`;

    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

            let data = JSON.parse(this.responseText);

            let resultsDiv = document.getElementById("divResults");
            resultsDiv.innerHTML = "";

            data.forEach(apt => {
                let div = document.createElement("div");
                div.className = "apartment-result";
                div.innerHTML = `<div><b>Title:</b> ${apt.title} <br><b>Description:</b> ${apt.description} <br><b>Bedrooms:</b> ${apt.numberofbedroom} <br><b>Monthly Rent:</b> $${apt.monthly_rent}</div>`;
                resultsDiv.appendChild(div);
            });
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

//Instantgram
function loadDoc(url, func) {
    let xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            func(xhttp.response);
        }
    }
    xhttp.open("GET", url);
    xhttp.send();
}
function list_files() {
    loadDoc('/listfiles', list_files_response)
}

function list_files_response(response) {
    let data = JSON.parse(response);
    let items = data["items"];
    let divResults = document.getElementById("divResults");
    divResults.innerHTML = '';

    for (let i = 0; i < items.length; i++) {
        let item = items[i];
        let imgElement = `<img src="${item.s3_path}" alt="${item.caption}" style="width: 128px; height: auto;">`;
        let captionElement = `<div>${item.caption}</div>`;

        divResults.innerHTML += `<div>${imgElement}${captionElement}</div>`;
    }
}

function upload_file() {
    let xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        if (xhttp.status != 200) {
            console.log("Error");
        } else {
            location.reload();
        }
    };

    xhttp.open('POST', '/uploadfile', true);
    var formData = new FormData();
    formData.append("file", document.getElementById('file').files[0]);
    formData.append("caption", document.getElementById('caption').value); // add title

    xhttp.send(formData);
}


function upload_file_response(response) {
    location.reload();
}
*/
