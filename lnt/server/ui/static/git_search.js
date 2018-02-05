function setAction(base_url) {
    var search_sha = document.getElementById("git-sha-search").value;
    console.log(base_url.toString() + search_sha.toString());
    document.getElementById("form").action = base_url.toString() + search_sha.toString();
}