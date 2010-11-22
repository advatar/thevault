/*global jQuery */
/* ****************************************************************************

	CJ Object Scaler jQuery Plug-In v2.1.2

	Copyright (c) 2010, Doug Jones. All rights reserved.
	
	Redistribution and use in source and binary forms, with or without
	modification, are permitted provided that the following conditions are met:
	
	Redistributions of source code must retain the above copyright notice, this
	list of conditions and the following disclaimer. Redistributions in binary
	form must reproduce the above copyright notice, this list of conditions and
	the following disclaimer in the documentation and/or other materials
	provided with the distribution. Neither the name BernieCode nor
	the names of its contributors may be used to endorse or promote products
	derived from this software without specific prior written permission. 
	
	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
	AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
	IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
	ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
	ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
	DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
	SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
	CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
	LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
	OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
	DAMAGE.
	
	For more information please visit www.cjboco.com.
	
	Example:
	
	jQuery("#myImage").cjObjectScaler({
		destElem: jQuery("#myParent"),	// option parent node. If not passed, it will use it's immediate parent
		method: "fit",					// fit | fill (default)
		fade: 500						// 0 no fade, positive integer fade duration
	}, function() {
		// custom callback function called when scaling is complete...
	});
	
	CHANGELOG
	
		v1.0	09/10/08 -	Initial Release
		v2.0	09/22/09 -	Coverted it to a jQuery plug-in
		v2.0.1	10/14/09 -	Fixed a bug where the scaling function
								wasn't being triggered, do to the
								image already being loaded.
								(Discovered by Ben Visser)
		v2.1	05/13/10 -	Added a new image onLoad check.
		v2.1.1	05/14/10 -	The border width check was failing in IE
								Big thanks to Funger for discovering this bug.
		v2.1.2 	06/10/10 -	It was recommended to add a callback function,
								which is called once the scaling is complete
								*Credit goes to Chris Bellew <Chris.Bellew@luxus.fi>
								for this. Thanks Chris!
	

**************************************************************************** */

/*
 jQuery('img.photo',this).imagesLoaded(myFunction)
 execute a callback when all images have loaded.
 needed because .load() doesn't work on cached images

 mit license. paul irish. 2010.
 webkit fix from Oren Solomianik. thx!

 callback function is passed the last image to load
 as an argument, and the collection as `this`
*/
(function ($) {
	jQuery.fn.imagesLoaded = function (callback) {
		var elems = this.filter('img'),
			len = elems.length;
		elems.bind('load', function () {
			if (--len <= 0) {
				callback.call(elems, this);
			}
		}).each(function () {
			// cached images don't fire load sometimes, so we reset src.
			if (this.complete || this.complete === undefined) {
				var src = this.src;
				// webkit hack from http://groups.google.com/group/jquery-dev/browse_thread/thread/eee6ab7b2da50e1f
				this.src = '#';
				this.src = src;
			}
		});
	};
})(jQuery);

/*
 CJ Object Scaler
*/
(function ($) {
	jQuery.fn.cjObjectScaler = function (options, callback) {

		/* 
			user variables (settings)
		***************************************/
		var settings = {
			// must be a jQuery object
			method: "fill",
			// the parent object to scale our object into
			destElem: null,
			// fit|fill
			fade: 0 // if positive value, do hide/fadeIn
		};

		/* 
			system variables
		***************************************/
		var sys = {
			// function parameters
			version: '2.1.2',
			elem: null
		};

		/* 
			scale the image
		***************************************/

		function scaleObj(obj) {

			// declare some local variables
			var destW = jQuery(settings.destElem).width(),
				destH = jQuery(settings.destElem).height(),
				ratioX, ratioY, scale, newWidth, newHeight, 
				borderW = parseInt(jQuery(obj).css("borderLeftWidth"), 10) + parseInt(jQuery(obj).css("borderRightWidth"), 10),
				borderH = parseInt(jQuery(obj).css("borderTopWidth"), 10) + parseInt(jQuery(obj).css("borderBottomWidth"), 10),
				objW = jQuery(obj).width(),
				objH = jQuery(obj).height();
				
			// check for valid border values. IE takes in account border size when calculating width/height so just set to 0
			borderW = isNaN(borderW) ? 0 : borderW;
			borderH = isNaN(borderH) ? 0 : borderH;
			
			// calculate scale ratios
			ratioX = destW / jQuery(obj).width();
			ratioY = destH / jQuery(obj).height();

			// Determine which algorithm to use
			if (!jQuery(obj).hasClass("cf_image_scaler_fill") && (jQuery(obj).hasClass("cf_image_scaler_fit") || settings.method === "fit")) {
				scale = ratioX < ratioY ? ratioX : ratioY;
			} else if (!jQuery(obj).hasClass("cf_image_scaler_fit") && (jQuery(obj).hasClass("cf_image_scaler_fill") || settings.method === "fill")) {
				scale = ratioX > ratioY ? ratioX : ratioY;
			}

			// calculate our new image dimensions
			newWidth = parseInt(jQuery(obj).width() * scale, 10) - borderW;
			newHeight = parseInt(jQuery(obj).height() * scale, 10) - borderH;
			
			// Set new dimensions & offset
			jQuery(obj).css({
				"width": newWidth + "px",
				"height": newHeight + "px",
				"position": "absolute",
				"top": (parseInt((destH - newHeight) / 2, 10) - parseInt(borderH / 2, 10)) + "px",
				"left": (parseInt((destW - newWidth) / 2, 10) - parseInt(borderW / 2, 10)) + "px"
			}).attr({
				"width": newWidth,
				"height": newHeight
			});

			// do our fancy fade in, if user supplied a fade amount
			if (settings.fade > 0) {
				jQuery(obj).fadeIn(settings.fade);
			}
			
			// cal the callback function if it was provided
			if (typeof callback === "function") {
				callback();
			}

		}

		/* 
			set up any user passed variables
		***************************************/
		if (typeof options === "object") {
			jQuery.extend(settings, options);
		} else if (typeof options === "function") {
			// be sure that they are passing options and not just a callback function.
			callback = options;
		}

		/* 
			main
		***************************************/
		return this.each(function () {
			
			sys.elem = this;

			// if they don't provide a destObject, use parent
			if (settings.destElem === null) {

				settings.destElem = jQuery(sys.elem).parent();
			}

			// need to make sure the user set the parent's position. Things go bonker's if not set.
			// valid values: absolute|relative|fixed
			if (jQuery(settings.destElem).css("position") === "static") {
				jQuery(settings.destElem).css({
					"position": "relative"
				});
			}

			// if our object to scale is an image, we need to make sure it's loaded before we continue.
			if (typeof sys.elem === "object" && typeof settings.destElem === "object" && typeof settings.method === "string") {
				
				// if the user supplied a fade amount, hide our image
				if (settings.fade > 0) {
					jQuery(sys.elem).hide();
				}
				
				if (sys.elem.nodeName === "IMG") {
					
					// to fix the weird width/height caching issue we set the image dimensions to be auto;
					jQuery(sys.elem).width("auto");
					jQuery(sys.elem).height("auto");
					
					// wait until the image is loaded before scaling
					jQuery(sys.elem).imagesLoaded(function () {
						scaleObj(this);
					});
					
				} else {
				
					// scale immediately
					scaleObj(jQuery(sys.elem));
				}

			} else {

				// wonky parameters were not passed
				alert("CJ Object Scaler could not initialize. Bad parameters.");
				return;

			}

		});

	};
})(jQuery);