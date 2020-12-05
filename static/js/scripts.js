$(document).ready(function () {
  $("#anythingSearch").on("keyup", function () {
    var value = $(this).val().toLowerCase();
    $("#myDIV *").filter(function () {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
  });
});

function search_inn() {
    var val = document.getElementById('id_inn').value;
    var reg = /[0-9]/;
    if (reg.test(val)) {
        requestURL = 'http://localhost:8000/inn_search/' + val
        const xhr = new XMLHttpRequest()
        xhr.open('GET', requestURL)
        xhr.onload = () => {
            var resultText = xhr.responseText;
            document.getElementById("id_company_name").value = resultText;
        }
        xhr.send()
    }
    else {
        document.getElementById("id_company_name").value = 'Не найдено';
    }
};

function handle_files(files) {
    var f = files[0];
    var reader = new FileReader();
    reader.onload = (function(theFile) {
        return function(e) {
            document.getElementById('load_file').innerHTML = ['<img class="design" src="', e.target.result,
                '" title="', escape(theFile.name), '">'].join('');
        };
    })(f);

    reader.readAsDataURL(f);
}

function load_company_file(files) {
    var f = files[0];
    var reader = new FileReader();
    reader.onload = (function(theFile) {
        return function(e) {
            document.getElementById('image_company').style.backgroundImage = "url('" + e.target.result +"')";
        };
    })(f);

    reader.readAsDataURL(f);
}

var ADDRESS_ID = 1;

function add_address() {
    var div = document.createElement('div');
    div.className = "row";
    div.id = 'div-address-' + ADDRESS_ID;
    div.innerHTML = ['<div class="col-12 col-lg-6"><div class="form-group"><input type="text" name="address',
        '" class="textinput textInput form-control" required=""></div></div><div class="col-12 ',
        'col-lg-6"><div class="form-group form-row"><div class="mr-3"><input type="date" name="date',
        '" autofocus="" autocapitalize="none" maxlength="255" ',
        'class="textinput textInput form-control" required="" id="id_date', '"></div><div>',
        '<input type="time" name="time', '" autofocus="" autocapitalize="none" ',
        'maxlength="255" class="textinput textInput form-control" required="" id="id_time',
        '"></div><div class="text-secondary p-2"><i class="far fa-trash-alt" onclick="remove_address(',
        "'div-address-", ADDRESS_ID,"'", ')"></i></div></div>'].join('');
    ADDRESS_ID += 1;
    document.getElementById('address-list').insertBefore(div, null);
}

function add_address_prod(prod_id) {
    var template = document.getElementById('template-address-' + prod_id);
    var div = document.createElement('div');
    div.className = "row";
    div.id = 'div-address-' + ADDRESS_ID;
    div.innerHTML = [template.innerHTML, '<div class="text-secondary p-2 h6"><i class="far fa-trash-alt"',
        'onclick="remove_address(', "'div-address-", ADDRESS_ID, "'", ')"></i></div>'].join('');
    ADDRESS_ID += 1;
    document.getElementById('address-list-'+prod_id).insertBefore(div, null);
}

function add_address_company() {
    var div = document.createElement('div');
    div.className = "form-inline";
    div.id = 'div-address-' + ADDRESS_ID;
    div.innerHTML = ['<input type="text" class="form-control col-10 col-lg-8" name="address">',
        '<div class="text-secondary col-2 p-2 pt-3 pl-3 h6"><i class="far fa-trash-alt"',
        'onclick="remove_address(', "'div-address-", ADDRESS_ID, "'", ')"></i></div>'].join('');
    ADDRESS_ID += 1;
    document.getElementById('address-list').insertBefore(div, null);
}

function remove_address(address_id) {
    var address = document.getElementById(address_id);
    address.remove()
}