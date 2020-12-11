$(document).ready(function () {
    $("#anythingSearch").on("keyup", function () {
        var value = $(this).val().toLowerCase();
        $("#myDIV *").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
});

function help_search() {
    var a, i;
    var input = document.getElementById("search");
    var filter = input.value.toUpperCase();
    var div = document.getElementById("question_list");
    var qList = div.getElementsByClassName("pb-2 ml-5");

    for (i = 0; i < qList.length; i++) {
        a = qList[i].getElementsByTagName("div")[0].getElementsByTagName("a")[0];
        if (a.innerHTML.toUpperCase().indexOf(filter) > -1) {
            qList[i].style.display = "";
        } else {
            qList[i].style.display = "none";
        }
    }
}

function nav_search() {
    var input = document.getElementById("main_search");
    document.getElementById("btn_search").href = '/help/#' + input.value;
}

if (window.location.pathname == '/help/') {
    var hash = window.location.hash;
    document.getElementById("search").value = decodeURI(hash.slice(1));
    help_search();
}

if (window.location.pathname.slice(0, 9) == '/product/') {
    if (window.location.hash == '#successful') {
        document.getElementById("successful_model").style.display = "block";
    }
}

if (window.location.pathname == '/new_orders/') {
    if (window.location.hash == '#successful') {
        document.getElementById("add_proposal_model").style.display = "block";
    }
}

if (window.location.pathname == '/orders/') {
    if (window.location.hash == '#add_order') {
        document.getElementById("add_order_model").style.display = "block";
    }
    if (window.location.hash == '#add_offer') {
        document.getElementById("add_offer_model").style.display = "block";
    }
}

function cancel_order(order_id, context) {
    document.getElementById("cancel_order_url").href = "/cancel_order/" + order_id + "/" + context
    document.getElementById("cancel_order_model").style.display = "block";
}

function split_order(order_id, offer) {
    document.getElementById("split_order_url_no").href = "/choose_offer/" + order_id + "/" + offer
    document.getElementById("split_order_url_yes").href = "/split_order/" + order_id + "/" + offer
    document.getElementById("split_order_model").style.display = "block";
}

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

function handle_files(files, num) {
    var f = files[0];
    var reader = new FileReader();
    reader.onload = (function(theFile) {
        return function(e) {
            document.getElementById('load_file-' + num).innerHTML = ['<img class="design" src="', e.target.result,
                '" title="', escape(theFile.name), '">'].join('');

            document.getElementById('label-' + num).innerHTML = escape(theFile.name)
        };
    })(f);

    reader.readAsDataURL(f);
}

function set_design_page(next, now) {
    document.getElementById('div-design-' + now).style.display = 'none';
    document.getElementById('div-design-' + next).style.display = 'block';
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
    div.innerHTML = ['<input type="text" class="form-control col-10 col-lg-8" name="address" required>',
        '<div class="text-secondary col-2 p-2 pt-3 pl-3 h6"><i class="far fa-trash-alt"',
        'onclick="remove_address(', "'div-address-", ADDRESS_ID, "'", ')"></i></div>'].join('');
    ADDRESS_ID += 1;
    document.getElementById('address-list').insertBefore(div, null);
}

function remove_address(address_id) {
    var address = document.getElementById(address_id);
    address.remove()
}