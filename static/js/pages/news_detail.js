$(document).ready(function() {

  const $content = $('#content');
  const $tocList = $('.right-directory ul');
  let idCounter = 1;

  $content.find('.ql-size-huge, .ql-size-large').each(function () {
    const $el = $(this);
    const text = $el.text().trim();
    const id = 'title-' + idCounter++;
    $el.attr('id', id);

    const $li = $('<li></li>');
    const isHuge = $el.hasClass('ql-size-huge');
    const $a = $('<a href="#"></a>')
      .addClass(isHuge ? 'b-title' : 's-title')
      .append(
        isHuge
          ? $('<h2></h2>').text(text)
          : $('<h3></h3>').text(text)
      )
      .on('click', function (e) {
        e.preventDefault();

        if ($(window).width() <= 767) {
            $('html, body').animate({ scrollTop: $('#' + id).offset().top - 65 }, 400);
        } else if ($(window).width() <= 999) {
            $('html, body').animate({ scrollTop: $('#' + id).offset().top - 65 }, 400);
        } else if ($(window).width() <= 1599) {
            $('html, body').animate({ scrollTop: $('#' + id).offset().top - 85 }, 400);
        } else {
            $('html, body').animate({ scrollTop: $('#' + id).offset().top - 105 }, 400);
        }


      });

    $li.append($a);
    $tocList.append($li);
  });

  // 如果沒有任何標題 拿掉此element

  if ($('ul#toc li').length == 0){
    $('.right-directory').remove()
  }


    $('.mb-cbtn').on('click', function() {
        $('.mb-cbtn').toggleClass('active');
        $('.right-directory ul').slideToggle();
    });

    // 當視窗改變尺寸時
    $(window).on('resize', function() {
        if ($(window).width() > 768) {
            $('.right-directory ul').show(); // 桌面版顯示
        } else {
            if (!$('.mb-cbtn').hasClass('active')) {
                $('.right-directory ul').hide(); // 手機版預設隱藏
            }
        }
    }).trigger('resize'); // 頁面載入時也執行一次
});