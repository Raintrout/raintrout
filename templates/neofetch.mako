<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">
<style>
${style}
</style>
<rect width="985px" height="530px" fill="${background_color}" rx="15"/>
<image 
  href="https://astropixels.com/diffusenebulae/images/M42-02-TMAPw.jpg"
  height="500" width="360"
  x="15" y="30"
  />
<text x="15" y="30" fill="#FFFFFF" tag="${text_color}" class="ascii">
<!-- image size (375,500) maybe add tarot card or something here in the future-->
 % for i, line in enumerate(ascii_lines):
   <tspan x="15" y="${(i*20)+30}">${line}</tspan>
 % endfor
</text>
<text x="390" y="30" fill="#c9d1d9">
 % for line in lines:
    ${line}
 % endfor
</text>
</svg>