import zipfile
import xml.etree.ElementTree as ET

ns = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

with zipfile.ZipFile(r'C:\Users\imja3\Downloads\PROJECT.pptx') as z:
    for i in range(1, 11):
        xml_content = z.read(f'ppt/slides/slide{i}.xml')
        root = ET.fromstring(xml_content)
        pics = root.findall('.//p:pic', ns)
        shapes = root.findall('.//p:sp', ns)
        print(f'=== Slide {i} ===')
        for pic in pics:
            xfrm = pic.find('.//a:xfrm', ns)
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                x = int(off.get('x')) / 914400 if off is not None else 0
                y = int(off.get('y')) / 914400 if off is not None else 0
                cx = int(ext.get('cx')) / 914400 if ext is not None else 0
                cy = int(ext.get('cy')) / 914400 if ext is not None else 0
                print(f'  Picture: pos=({x:.2f}", {y:.2f}"), size=({cx:.2f}" x {cy:.2f}") -> aspect ratio {cx/cy:.2f}' if cy else '0')
        for sp in shapes:
            # check if it is a placeholder or blank box
            txt = ''.join(sp.itertext()).strip()
            xfrm = sp.find('.//a:xfrm', ns)
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                x = int(off.get('x')) / 914400 if off is not None else 0
                y = int(off.get('y')) / 914400 if off is not None else 0
                cx = int(ext.get('cx')) / 914400 if ext is not None else 0
                cy = int(ext.get('cy')) / 914400 if ext is not None else 0
                if not txt and cx > 1 and cy > 1:
                    print(f'  Empty Shape: pos=({x:.2f}", {y:.2f}"), size=({cx:.2f}" x {cy:.2f}") -> aspect ratio {cx/cy:.2f}' if cy else '0')
