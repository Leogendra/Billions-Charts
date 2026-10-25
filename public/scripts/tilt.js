var VanillaTilt = (function () {
    'use strict';

    /**
     * Created by Sergiu Șandor (micku7zu) on 1/27/2017.
     * Original idea: https://github.com/gijsroge/tilt.js
     * MIT License.
     * Version 1.8.1
     */

    class VanillaTilt {
        constructor(element, settings = {}) {
            if (!(element instanceof Node)) {
                throw ("Can't initialize VanillaTilt because " + element + " is not a Node.");
            }

            this.width = null;
            this.height = null;
            this.clientWidth = null;
            this.clientHeight = null;
            this.left = null;
            this.top = null;

            this.transitionTimeout = null;
            this.updateCall = null;
            this.event = null;

            this.updateBind = this.update.bind(this);
            this.resetBind = this.reset.bind(this);

            this.element = element;
            this.settings = this.extendSettings();

            this.reverse = this.settings.reverse ? -1 : 1;
            this.resetToStart = VanillaTilt.isSettingTrue(this.settings["reset-to-start"]);

            this.elementListener = this.getElementListener();

            this.addEventListeners();
            this.reset();

            if (this.resetToStart === false) {
                this.settings.startX = 0;
                this.settings.startY = 0;
            }
        }

        static isSettingTrue(setting) {
            return setting === "" || setting === true || setting === 1;
        }

        /**
         * Method returns element what will be listen mouse events
         * @return {Node}
         */
        getElementListener() {

            if (typeof this.settings["mouse-event-element"] === "string") {
                const mouseEventElement = document.querySelector(this.settings["mouse-event-element"]);

                if (mouseEventElement) {
                    return mouseEventElement;
                }
            }

            if (this.settings["mouse-event-element"] instanceof Node) {
                return this.settings["mouse-event-element"];
            }

            return this.element;
        }

        /**
         * Method set listen methods for this.elementListener
         * @return {Node}
         */
        addEventListeners() {
            this.onMouseEnterBind = this.onMouseEnter.bind(this);
            this.onMouseMoveBind = this.onMouseMove.bind(this);
            this.onMouseLeaveBind = this.onMouseLeave.bind(this);
            this.onWindowResizeBind = this.onWindowResize.bind(this);

            this.elementListener.addEventListener("mouseenter", this.onMouseEnterBind);
            this.elementListener.addEventListener("mouseleave", this.onMouseLeaveBind);
            this.elementListener.addEventListener("mousemove", this.onMouseMoveBind);
        }

        /**
         * Method remove event listeners from current this.elementListener
         */
        removeEventListeners() {
            this.elementListener.removeEventListener("mouseenter", this.onMouseEnterBind);
            this.elementListener.removeEventListener("mouseleave", this.onMouseLeaveBind);
            this.elementListener.removeEventListener("mousemove", this.onMouseMoveBind);
        }

        onMouseEnter() {
            this.updateElementPosition();
            this.element.style.willChange = "transform";
            this.setTransition();
        }

        onMouseMove(event) {
            if (this.updateCall !== null) {
                cancelAnimationFrame(this.updateCall);
            }

            this.event = event;
            this.updateCall = requestAnimationFrame(this.updateBind);
        }

        onMouseLeave() {
            this.setTransition();

            if (this.settings.reset) {
                requestAnimationFrame(this.resetBind);
            }
        }

        reset() {
            this.onMouseEnter();

            this.event = {
                clientX: this.left + ((this.settings.startX + this.settings.max) / (2 * this.settings.max) * this.width),
                clientY: this.top + ((this.settings.startY + this.settings.max) / (2 * this.settings.max) * this.height)
            };

            this.update();
        }

        getValues() {
            let x, y;
            
            x = (this.event.clientX - this.left) / this.width;
            y = (this.event.clientY - this.top) / this.height;

            x = Math.min(Math.max(x, 0), 1);
            y = Math.min(Math.max(y, 0), 1);

            let tiltX = (this.reverse * (this.settings.max - x * this.settings.max * 2)).toFixed(2);
            let tiltY = (this.reverse * (y * this.settings.max * 2 - this.settings.max)).toFixed(2);
            let angle = Math.atan2(this.event.clientX - (this.left + this.width / 2), -(this.event.clientY - (this.top + this.height / 2))) * (180 / Math.PI);

            return {
                tiltX: tiltX,
                tiltY: tiltY,
                percentageX: x * 100,
                percentageY: y * 100,
                angle: angle
            };
        }

        updateElementPosition() {
            let rect = this.element.getBoundingClientRect();

            this.width = this.element.offsetWidth;
            this.height = this.element.offsetHeight;
            this.left = rect.left;
            this.top = rect.top;
        }

        update() {
            if (window.innerWidth < 800) { return; }
            let values = this.getValues();

            this.element.style.transform = "perspective(1000px) " +
                "rotateX(" + (this.settings.axis === "x" ? 0 : values.tiltY) + "deg) " +
                "rotateY(" + (this.settings.axis === "y" ? 0 : values.tiltX) + "deg) " +
                "scale3d(" + (values.tiltY != 0 ? 1.1 : 1) + ", " + (values.tiltY != 0 ? 1.1 : 1) + ", 1)";

            this.element.dispatchEvent(new CustomEvent("tiltChange", {
                "detail": values
            }));

            this.updateCall = null;
        }

        updateClientSize() {
            this.clientWidth = window.innerWidth
                || document.documentElement.clientWidth
                || document.body.clientWidth;

            this.clientHeight = window.innerHeight
                || document.documentElement.clientHeight
                || document.body.clientHeight;
        }

        onWindowResize() {
            this.updateClientSize();
        }


        setTransition() {
            clearTimeout(this.transitionTimeout);
            this.element.style.transition = this.settings.speed + "ms " + this.settings.easing;
            this.transitionTimeout = setTimeout(() => {
                this.element.style.transition = "";
            }, this.settings.speed);

        }

        extendSettings() {
            let newSettings = {
                reverse: true,
                max: 3,
                startX: 0,
                startY: 0,
                easing: "cubic-bezier(.03,.98,.52,.99)",
                speed: 300,
                transition: true,
                axis: null,
                "mouse-event-element": null,
                reset: true,
                "reset-to-start": true
            };

            return newSettings;
        }

        static init(elements, settings) {
            if (elements instanceof Node) {
                elements = [elements];
            }

            if (elements instanceof NodeList) {
                elements = [].slice.call(elements);
            }

            if (!(elements instanceof Array)) {
                return;
            }

            elements.forEach((element) => {
                if (!("vanillaTilt" in element)) {
                    element.vanillaTilt = new VanillaTilt(element, settings);
                }
            });
        }
    }

    if (typeof document !== "undefined") {
        window.VanillaTilt = VanillaTilt;

        VanillaTilt.init(document.querySelectorAll("[data-tilt]"));
    }

    return VanillaTilt;

}());