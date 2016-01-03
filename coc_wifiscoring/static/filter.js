// Adds column filters to the result tables

window.onload = function() {
  var table = document.getElementById("resultTable");
  var tbody = table.firstElementChild;
  
  var thead = tbody.firstElementChild;
  var trs = tbody.children;
  
  var filter = function(col, input) {
    var searchText = input.value.toLowerCase();
      
    for(var i = 1; i < trs.length; ++i) {
        var display = "";
        
        var colChild = trs[i].children[col];
        if (colChild && colChild.innerHTML.toLowerCase().indexOf(searchText) === -1)
            display = "none";
        
        trs[i].style.display = display;
    }
  };
  
  for (var i = 1; i < thead.children.length; ++i) {
      if (thead.children[i].innerHTML === "Name" || thead.children[i].innerHTML === "Club") {
          var input = document.createElement("input");
          input.setAttribute("placeholder", "(enter a filter)");
          input.oninput = (function(i, input) { return function() {
              filter(i, input);
          }})(i, input);
          
          thead.children[i].appendChild(document.createElement("br"));
          thead.children[i].appendChild(input);
      }
  }
};
