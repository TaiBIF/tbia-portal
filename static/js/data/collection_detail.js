
let slideIndex = 1;

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
