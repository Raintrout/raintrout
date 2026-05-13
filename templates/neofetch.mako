<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="${svg_width}px" height="${svg_height}px" font-size="${font_size}px">
<style>
${style}
</style>
<rect width="${svg_width}px" height="${svg_height}px" fill="${background_color}" rx="${border_radius}"/>
<text x="${ascii_x}" y="${ascii_y}" fill="${text_color}" class="ascii">
<!-- image size (375,500) maybe add tarot card or something here in the future-->
 % for i, line in enumerate(ascii_lines):
   <tspan x="${ascii_x}" y="${(i * line_height) + ascii_y}">${line}</tspan>
 % endfor
</text>
<path d="${mountain_path}" fill="${mountain_color}"/>
${work_timeline_svg}
<text x="${stats_x}" y="${stats_y}" fill="${stats_text_color}">
 % for line in lines:
    ${line}
 % endfor
</text>
</svg>
