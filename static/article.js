/* WERSJA 26.05.2026 */
// po kliknięciu w obrazek na marginesie pojawia się fullscreen modal

/* WERSJA 22.12.2023 */
// plik z funkcjami do tresci artykulow (przesuwa blockquote na margines oraz chowa i robi chowalne wskazowki)

$( document ).ready(function() {
	  if ($(window).width() >= 1150) {
	  	  var i=0;
	  	  var bottom = 0;
		  $('.article-input-main-text .span-blockquote-ref').each(function() {
				var blockid = $(this).attr('id').substring(5);
				var blockquote = $('blockquote#'+blockid);
				$('.article-input-margin').append(blockquote);
	  		    blockquote.hide();
		  });

  		  setTimeout(() => {
			  	$('p').each(function() {
					console.log("WINDA: "+$(window).width());
					console.log("JA _ PRZED  "+$(this).width());
					if ($(this).width() > $( window ).width()) $(this).width($(window).width());
					console.log("JA _ PO "+$(this).width());
				});
			
			    var bottom=0;
		  	    $('span.span-blockquote-ref').each(function() {
					var blockid = $(this).attr('id').substring(5);
					var blockquote = $('blockquote#'+blockid);
					var position = $(this).position();
				  	var topik = position.top-25;
				  	var where = (topik < bottom ? bottom : topik);
				  	blockquote.css({position: "absolute", top: where});
					blockquote.position(where);
					blockquote.show();
				    bottom = where + blockquote.outerHeight(true) + 10;
				})
	  		    $('.article-input-margin').show('slow');
	  		    
				if ($('.article-input-div').position().top + $('.article-input-div').outerHeight() < bottom+200)
					if ($('.article-input-div').outerHeight() < bottom - $('.article-input-div').position().top)
	  				    $('.article-input-div').height(bottom - $('.article-input-div').position().top);
  		  },500)

	  } else {
		  	$('.article-input-main-text > p').each(function() {
				if ($(this).width() > $( window ).width()-60) {
					$(this).width($(window).width()-60);
				}
			});
		  	$('.article-input-main-text blockquote').each(function() {
				if ($(this).width() > $( window ).width()-120) {
					$(this).width($(window).width()-120);
				}
			});
		  	$('.article-input-main-text div').each(function() {
				if ($(this).width() > $( window ).width()-60) {
					$(this).width($(window).width()-60);
				}
			});
	  }
  
	$(function() {
		$('section.expandable > div.content-wrapper').hide();
		$('section.expandable > header').click(function(){
			$(this).parents('section.expandable').find('div.content-wrapper').toggle();});

		$('div.exercise > div.answer-content').hide();
		$('div.exercise > header.answer').click(function(){
			console.log("KLIK!");
			$(this).parents('div.exercise').find('div.answer-content').toggle('fast');});
	});

	// fullscreen lightbox dla wszystkich obrazkow w artykule (desktop only)
	// wykluczamy img.math-inline (drobne rownania).
	// uzywamy .click() + natywnego addEventListener bo strona dziala na
	// starej jQuery (<1.7) bez .on()/.off()
	if ($(window).width() >= 1150) {
		$('.article-input img').not('.math-inline').click(function() {
			var overlay = $('<div class="image-lightbox"></div>');
			overlay.append($('<img>').attr('src', $(this).attr('src')));
			function onKey(e) {
				if (e.key === 'Escape') close();
			}
			function close() {
				overlay.remove();
				document.removeEventListener('keydown', onKey);
			}
			overlay.click(close);
			document.addEventListener('keydown', onKey);
			$('body').append(overlay);
		});
	}
})

