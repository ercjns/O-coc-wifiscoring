// Adds column filters to the result tables

window.onload = function() {
  var filterColumns = ["Name", "Club"];

  var currentFilter = {};

  var table = document.getElementById("resultTable");
  var tbody = table.firstElementChild;
  
  var thead = tbody.firstElementChild;
  var trs = tbody.children;
  
  var filter = function(col, input) {
      currentFilter[col] = input.toLowerCase();

      for(var i = 1; i < trs.length; ++i) {
          var display = "";

          var tr = trs[i];

          Object.keys(currentFilter).forEach(function(filterCol) {
              var colChild = tr.children[filterCol];
              if (colChild && colChild.innerHTML.toLowerCase().indexOf(currentFilter[filterCol]) === -1)
                  display = "none";
          });

          trs[i].style.display = display;
      }
  };
  
  for (var i = 1; i < thead.children.length; ++i) {
      var text = thead.children[i].innerHTML;

      if (filterColumns.indexOf(text) !== -1) {
          var input = document.createElement("input");
          input.setAttribute("placeholder", "(enter a filter)");
          input.oninput = (function(i, input) { return function() {
              filter(i, input.value);
          }})(i, input);
          
          thead.children[i].appendChild(document.createElement("br"));
          thead.children[i].appendChild(input);
      }
  }
};
