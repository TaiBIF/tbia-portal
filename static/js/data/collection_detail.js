
let slideIndex = 1;

const issue_messages = {
  '1': gettext("請協助確認您所搜尋的學名、本筆資料顯示的學名、以及來源資料庫使⽤學名是否皆已在<a href='https://taicol.tw' target='_blank'>臺灣物種名錄</a>中收錄，若無收錄，請至臺灣物種名錄進行<a href='https://taicol.tw/submit' target='_blank'>物種登錄</a>。如您的問題與學名是否收收錄至臺灣物種名錄無關，問題類型請選擇「其他」選項進行回報"),
  '2': gettext('請提供詳細座標錯誤說明'),
  '3': gettext('請提供詳細問題說明')
};

$(function () {
    if ($('input[name=has_media]').val()=='t'){
        showSlides(slideIndex);
    }

    $('.arr-left').on('click', function(){
        plusSlides(-1)
    })

    $('.arr-right').on('click', function(){
        plusSlides(+1)
    })

    $('.open-ref').on('click', function(){
        window.open($(this).data('ref'))
    })

    $('.right_area .img-container').on('click', function(){
        $('.taxon-pop').removeClass('d-none')
    })


    $('.issue_button').on('click', function () {
        $('.issue-pop').removeClass('d-none')
    })

    let selectBoxIssue = new vanillaSelectBox("#issue_type", {
        "placeHolder": $('#issue_type').attr('placeholder'), search: false, disableSelectAll: true,
    });

    $('#issue_type').on('change', function (e) {
        if ($('#btn-group-issue_type .vsb-menu ul li.active').length > 0) {
            $('#btn-group-issue_type button span.title').addClass('black').removeClass('color-707070')
        } else {
            $('#btn-group-issue_type button span.title').addClass('color-707070').removeClass('black')
        }

        e.preventDefault()
        let res = selectBoxIssue.getResult()[0]

        // 依照選擇的類型跳出說明文字
        $('#issue_message').html(issue_messages[res])
        $('.issue-pop .content_area, .issue-pop .email_area, .issue-pop .send, .issue-pop .g-recaptcha').toggleClass('d-none', res === '1');

    })


    $('.issue-pop .send').on('click', function(){

        if ((!$('input[name=is_authenticated]').val() && !window.has_grecaptcha) | 
            (!validateEmail($('#issue_form input[name=email]').val()) ) |
            (!$('#issue_form textarea[name=content]').val())) {
            alert(gettext('請完整填寫表格並檢查Email格式是否正確'))
        } else {

            $.ajax({
                url: "/send_issue",
                data: $('#issue_form').serialize() + '&csrfmiddlewaretoken=' + $csrf_token + '&url=' + window.location.href, 
                type: 'POST',
            })
            .done(function (response) {
                alert(gettext('謝謝您的回報！'))
                $('.issue-pop').addClass('d-none')
            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                $('.issue-pop').addClass('d-none')
            })

        }
    })

})

function addClass(element, className){
    element.className += ' ' + className;   
}

function removeClass(element, className) {
    element.className = element.className.replace(
    new RegExp('( |^)' + className + '( |$)', 'g'), ' ').trim();
}

function plusSlides(n) {
    showSlides(slideIndex += n);
}

function currentSlide(n) {
    showSlides(slideIndex = n);
}

function showSlides(n) {
    let i;
    let slides = document.getElementsByClassName("mySlides");
    if (n > slides.length) {slideIndex = 1}    
    if (n < 1) {slideIndex = slides.length}
    for (i = 0; i < slides.length; i++) {
        removeClass(slides[i], 'd-none')
        removeClass(slides[i], 'd-block')
        addClass(slides[i], 'd-none')
    }
    removeClass(slides[slideIndex-1], 'd-none')
    addClass(slides[slideIndex-1], 'd-block')

    // 修改pop裡面的內容
    $('.taxon-pop .picbox').html($('.right_area .picbox.d-block').html())
}


let redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

if (($('input[name="lat"]').val()!="None")&($('input[name="lon"]').val()!="None")) {
    let map = L.map('map').setView([$('input[name="lat"]').val(), $('input[name="lon"]').val()],6);
    L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    L.marker([$('input[name="lat"]').val(), $('input[name="lon"]').val()], {icon: redIcon}).addTo(map);
} else {
    let map = L.map('map').setView([23.5, 121.2], 7);
    L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}
