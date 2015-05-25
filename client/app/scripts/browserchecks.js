var isBrowserCompatible = function() {
  return !(bowser.msie && bowser.version <= 8);
};
