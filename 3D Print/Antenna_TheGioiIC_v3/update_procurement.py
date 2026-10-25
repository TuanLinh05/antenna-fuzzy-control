"""Record the live product-page observations made on 2026-10-24.
No purchase is made. Stock is an observation, not a reservation.
"""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parent
old=json.loads((ROOT.parent/'Antenna_TheGioiIC_v2'/'procurement.json').read_text(encoding='utf-8'))
stocks={'IC373':60,'IC5255':1,'IC7387':46,'IC20188':46,'IC15606':1599,'IC17522':49,
 'IC10179':3481,'IC10152':3975,'IC10153':16047,'IC10154':2150,'IC10155':9150,
 'IC10156':4553,'IC10107':2280,'IC9122':12903,'IC8318':363,'IC33241':265}
items=old['items']
for q in items:
    q.update(stock=stocks[q['sku']],verified_date='2026-10-24',category='mechanical',minimum=1,multiple=1)
    if q['sku'] in ('IC10152','IC10153','IC10154','IC10155'):q.update(minimum=10,multiple=5)
    if q['sku'] in ('IC9122','IC8318'):q.update(minimum=20,multiple=10)
    if q['sku']=='IC10107':q.update(minimum=20,multiple=10)
    if q['sku']=='IC33241':q.update(minimum=10,multiple=5)
    if q['sku']=='IC17522':q['notes']='Cắt 120 +40 +30 mm; chừa tối đa 10 mm cho đường cắt và sửa đầu. Dũa mặt phẳng ở các vị trí truyền động theo hướng dẫn V3.'
    if q['sku']=='IC10152':q.update(required=4,notes='Adapter ép trục 1; mặt encoder 3 kèm đệm in 1 mm, vào ren encoder 3 mm danh định. Kiểm tra chiều sâu ren thực.')
    if q['sku']=='IC10155':q.update(required=6,notes='Vòng chặn 2; gá encoder vào đế 4.')
    if q['sku']=='IC9122':q.update(required=28,notes='24 vị trí V2 +4 đai ốc dưới gá encoder. AF5.5 mm danh định.')
    if q['sku']=='IC10179':q['notes']='Khung 20 vị trí, dùng lại ốc đang có nếu đúng M4x20 DIN912. Không cần mua dòng này nếu đã đủ.'


def add(sku,name,req,buy,price,stock,slug,notes,category='electrical',minimum=1,multiple=1):
    items.append(dict(item=name,sku=sku,required=req,purchase=buy,price=price,stock=stock,
        url='https://www.thegioiic.com/'+slug,notes=notes,verified_date='2026-10-24',
        category=category,minimum=minimum,multiple=multiple))


add('IC3636','Encoder LPD3806-600BM NPN 600P/R',1,1,318060,123,
    'lpd3806-600bm-rotary-encoder-600-xung-npn-5-24vdc',
    'Trục 6x13; thân D38; boss20x5; 3 lỗ M3 PCD28 hoặc30. Cấp5V; A/B kéo lên3.3V. Thân dài45mm là bao dự phòng, không phải kích thước nhà sản xuất.', 'mechanical')
add('IC20164','Khớp nối cứng D14 L25 lỗ6-8',1,1,11400,24,
    'khop-noi-truc-cung-dai-25mm-lo-truc-6-8',
    'Khớp đo encoder, không đỡ tải bàn xoay. Căn đồng tâm trước khi siết; vít hãm đi kèm cần kiểm tra khi nhận.', 'mechanical')
add('IC7010','TB6600 driver stepper 42-57 4A',1,1,116046,275,
    'tb6600-mach-dieu-khien-dong-co-buoc-42-57-4a',
    'Cấp12V; chọn1/16 (3200 xung/vòng motor), bắt đầu mức dòng1.0A rồi thử tối đa1.5A theo bảng thực. Tín hiệu qua transistor, không nối3.3V trực tiếp vào opto5V.')
add('IC2723','Adapter kín 12V5A DC5525',1,1,83220,142,
    'nguon-adapter-12v-5a-dau-dc-5-5x2-5mm-dai-1m-co-led','Nguồn chính60W. Dùng jack cái5525 đúng2.5mm; đo cực tính trước khi đấu.')
add('IC19734','MP2482 module hạ áp 5V5A',1,1,35340,292,
    'mp2482-mach-on-ap-5v-5a','Vào7-30V, ra5V theo cửa hàng. Nhánh servo và encoder, có tụ1000uF. 5A là mức công bố; kiểm tra sụt áp và nhiệt dưới tải thực.')
add('IC2033','2N3904 NPN TO92',3,20,342,2260,
    '2n3904-transistor-npn-40v-0-2a-3-chan-to-92','Ba kênh STEP, DIR, đệm servo. Tra đúng E/B/C theo datasheet ON Semiconductor; không suy ra từ hình vỏ.',minimum=20,multiple=10)
add('IC921','Điện trở1k 1/4W 5%',5,50,55,18500,
    'dien-tro-1-kohm-1-4w-5-4-vong-mau','3 điện trở base transistor; 2 nối tiếp A/B encoder.',minimum=50,multiple=50)
add('IC923','Điện trở4k7 1/4W 5%',3,50,55,20350,
    'dien-tro-4-7-kohm-1-4w-5-4-vong-mau','2 kéo A/B lên3.3V; 1 kéo tín hiệu servo lên5V.',minimum=50,multiple=50)
add('IC925','Điện trở10k 1/4W 5%',3,50,55,10550,
    'dien-tro-10-kohm-1-4w-5-4-vong-mau','Base-emitter kéo xuống cho3 transistor.',minimum=50,multiple=50)
add('IC4475','Tụ hóa1000uF16V xuyên lỗ',1,2,1596,271,
    'tu-hoa-1000uf-16v-8x16mm-xuyen-lo','Lắp song song5V/GND sát đầu cấp servo, đúng cực. Mua1 dự phòng.')
add('IC37942','Dây silicon18AWG đen',2,2,15960,1706,
    '18awgx1-day-dien-silicon-chiu-nhiet-sieu-mem-mau-den-loai-tot','Đơn vị mét; dây GND nguồn, đi theo hình sao.')
add('IC37941','Dây silicon18AWG đỏ',2,2,15960,372,
    '18awgx1-day-dien-silicon-chiu-nhiet-sieu-mem-mau-do-loai-tot','Đơn vị mét; nhánh12V/5V phân biệt và đánh dấu rõ.')
add('IC7157','PCB hàn test FR4 5x7cm',1,1,6703,1825,
    'fr4-pcb-han-test-board-5x7cm-phu-xanh-1-mat','Hàn mạch đệm và phân phối tín hiệu. Nhánh công suất dùng dây đồng18AWG, không dùng pad mảnh làm đường dòng servo.')
add('IC22930','Hàng rào đực2.54mm40chân đồng mạ niken',2,2,1596,2839,
    'hang-rao-duc-don-2-54mm-40-chan-1-hang-cao-11-2mm-xuyen-lo-chan-dong-ma-niken','Cắt header cho board và đầu servo. Hàn chắc các chân cấp nguồn.')
add('IC2553','Dây bẹ cái-cái30cm',10,20,570,16880,
    'day-be-cai-cai-dai-30cm','Giá theo từng sợi; chỉ dùng cho tín hiệu và dòng nhỏ của MCU, không cấp dòng servo qua dây Dupont.',minimum=10,multiple=10)
add('IC7741','Jack DC5525 cái kèm domino',1,1,4560,462,
    'dc5525-dau-noi-nguon-dc-cai-noi-day-kim-2-5mm-kem-domino','Khớp adapter5525; giữ lực kéo khỏi PCB, kiểm tra tiếp xúc và nhiệt khi chạy.')
add('IC1167','Domino KF128-2-V5mm10A',6,8,2850,17832,
    'kf128-2-v-domino-2-chan-thang-5mm-300v-10a-han-pcb-loai-tot','Nguồn vào, nguồn5V, encoder và các đầu dây. Mua2 dự phòng.')
add('IC3024','CP2102 USB-TTL UART',1,1,44460,578,
    'cp2102-mach-chuyen-doi-usb-to-ttl-uart','Nạp bằng bootloader UART hoặc ghi dữ liệu. TX/RX dùng mức3.3V; không cấp servo từ cổng này. Khi board đã cấp nguồn riêng chỉ nốiTX/RX/GND.')
add('IC2780','Ống co nhiệt4mm600V',1,1,2394,2967,
    'ong-co-nhiet-4mm-600v','Đơn vị mét. Cách điện từng mối nối; dây servo cần nối dài bằng dây mềm và chừa vòng dây, không kéo căng dây300mm có sẵn.')

optional=[dict(item='STM32F103C8T6 Micro USB',sku='IC4997',required=1,purchase=1,price=54720,stock=728,
    url='https://www.thegioiic.com/mach-stm32f103c8t6-micro-usb',minimum=1,multiple=1,
    verified_date='2026-10-24',notes='Chỉ mua nếu chưa có boardF103. Firmware chính choF103; F4 dùng lại lõi fuzzy sau khi port ngoại vi.')]
for q in items+optional:
    assert q['stock']>=q['purchase']>=q['required']
    assert q['purchase']>=q['minimum'] and q['purchase']%q['multiple']==0
    q['source_excerpt']=f"Hàng còn: {q['stock']}; Đơn giá: {q['price']} VND; Min: {q['minimum']}; Bội số: {q['multiple']}"
    q['verification_method']='Live visible product page in browser, SKU checked'
mechanical=sum(q['price']*q['purchase'] for q in items if q['category']=='mechanical')
electrical=sum(q['price']*q['purchase'] for q in items if q['category']=='electrical')
result=dict(verified_date='2026-10-24',currency='VND',mechanical_total_vnd=mechanical,
    electrical_total_vnd=electrical,system_total_vnd=mechanical+electrical,
    items=items,optional_items=optional,stock_reserved=False,
    excluded_products=[dict(sku='IC42490',reason='Store states Vin10-110V but also Vin-Vout>=25V; cannot accept at12V without clarification.'),
                       dict(sku='IC43522',reason='40cm jumper wire had no in-stock purchase; replaced by30cm IC2553.')],
    exclusions=['3D printing material, machining/filing labor, solder and general tools.','Existing STM32 board, or optional IC4997 separately.'])
(ROOT/'procurement.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'audit'/'stock_evidence_2026-10-24.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
with (ROOT/'hardware_BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['category','item','sku','required','purchase','price','stock','minimum','multiple','url','notes','verified_date']
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(items)
lines=['# BOM V3 - kiểm tra ngày24/10/2026','',
       'Tất cả mã trong bảng dưới được kiểm tra trực tiếp trên trang sản phẩm tại Thế Giới IC. Tồn kho là ảnh chụp tại thời điểm kiểm tra, không phải giữ hàng. Motor IC5255 chỉ còn1 chiếc.',
       '', '| Linh kiện | Mã/link | Cần | Đặt mua | Tồn | Giá/đơn vị | Thành tiền |','|---|---|---:|---:|---:|---:|---:|']
for q in items:
    lines.append(f"| {q['item']} | [{q['sku']}]({q['url']}) | {q['required']} | {q['purchase']} | {q['stock']} | {q['price']:,} | {q['price']*q['purchase']:,} |")
lines+=['',f'**Cơ khí: {mechanical:,}đ. Điện và vật tư: {electrical:,}đ. Tổng mua mới: {mechanical+electrical:,}đ.**',
        '', 'Giá chưa gồm vận chuyển, nhựa in và dụng cụ. Có đủ20 vítM4x20DIN912 thì có thể bỏ dòngIC10179, giảm32.832đ.',
        '',f"Board STM32 bạn có sẵn không nằm trong tổng. Nếu cần mua: [IC4997]({optional[0]['url']}), {optional[0]['price']:,}đ, còn{optional[0]['stock']} chiếc.",
        '', '## Lưu ý chọn đúng linh kiện','']
lines += [f"- **{q['sku']}**: {q['notes']}" for q in items]
lines+=['','Không thay bằng hàng hết kho hoặc loại cùng tên nhưng khác trục/điện áp. Các giá và tồn kho cũ ngày11/10 không còn là căn cứ mua.','',
        'Sản phẩmIC42490 bị loại vì thông số chênh áp mâu thuẫn; dây40cmIC43522 được thay bằng30cmIC2553. Không cần mua nguồnAC hở; adapter kín12V là nguồn điện lưới duy nhất.']
(ROOT/'DANH_SACH_MUA_THEGIOIIC.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(status='PASS_LIVE_SNAPSHOT',products=len(items),mechanical=mechanical,electrical=electrical,total=mechanical+electrical)))
