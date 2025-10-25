function SearchTable(inputId, tableId) {
    var input, filter, table, tr, td, i, txtValue;
    input = document.getElementById(inputId);
    filter = input.value.toUpperCase();
    table = document.getElementById(tableId);
    trs = table.getElementsByTagName("tr");  
    if(input===""){
        return;
    }
    for(let i=0; i<trs.length;i++){
        tr = trs[i]
        tds = tr.getElementsByTagName("td");
        for(let ii=0;ii<tds.length;ii++){
            td = tds[ii];
            txtValue = td.textContent || td.innerText;
            if(txtValue.toUpperCase().indexOf(filter) > -1) {
                tr.style.display = "";
                break;
            } else {
                tr.style.display = "none";
            }
        }
    }
}