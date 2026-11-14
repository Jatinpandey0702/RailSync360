import zipfile
import xml.etree.ElementTree as ET

ns = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

with zipfile.ZipFile(r'C:\Users\imja3\Downloads\PROJECT.pptx') as z:
    for i in range(1, 11):
        print(f"\n=================== SLIDE {i} ===================")
        xml_content = z.read(f'ppt/slides/slide{i}.xml')
        root = ET.fromstring(xml_content)
        for sp in root.findall('.//p:sp', ns):
            txt = ' '.join(''.join(p.itertext()).strip() for p in sp.findall('.//a:p', ns) if ''.join(p.itertext()).strip())
            xfrm = sp.find('.//a:xfrm', ns)
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                x = int(off.get('x')) / 914400 if off is not None else 0
                y = int(off.get('y')) / 914400 if off is not None else 0
                cx = int(ext.get('cx')) / 914400 if ext is not None else 0
                cy = int(ext.get('cy')) / 914400 if ext is not None else 0
                if txt:
                    print(f"Text Box: pos=({x:.2f}\", {y:.2f}\"), size=({cx:.2f}\" x {cy:.2f}\") | Text: {txt[:60]}...")
                else:
                    print(f"Empty Shape: pos=({x:.2f}\", {y:.2f}\"), size=({cx:.2f}\" x {cy:.2f}\")")
        for pic in root.findall('.//p:pic', ns):
            xfrm = pic.find('.//a:xfrm', ns)
            if xfrm is not None:
                off = xfrm.find('a:off', ns)
                ext = xfrm.find('a:ext', ns)
                x = int(off.get('x')) / 914400 if off is not None else 0
                y = int(off.get('y')) / 914400 if off is not None else 0
                cx = int(ext.get('cx')) / 914400 if ext is not None else 0
                cy = int(ext.get('cy')) / 914400 if ext is not None else 0
                print(f"Picture: pos=({x:.2f}\", {y:.2f}\"), size=({cx:.2f}\" x {cy:.2f}\")")
