# Mechanical Design and 3D Printing / Thiết kế cơ khí và in 3D

## English

**Start with [Antenna V5 Reinforced](Antenna_V5_Reinforced/README_START_HERE.md).** It is the current mechanical design for the stepper/TB6600, MT6701, and LD-1501MG configuration.

| Folder | Role |
| --- | --- |
| [`Antenna_V5_Reinforced/`](Antenna_V5_Reinforced/README_START_HERE.md) | Current design: reinforced servo carrier and open sensor mount |
| [`Antenna_V4_MT6701/`](Antenna_V4_MT6701/README_START_HERE.md) | Previous MT6701 design; geometry reference for V5 |
| [`Antenna_TheGioiIC_v3/`](Antenna_TheGioiIC_v3/README_START_HERE.md) | Earlier prototype and its assembly/procurement documents |
| `Antenna_TheGioiIC_v2/` | Earlier prototype retained for historical comparison |

For V5, use the [A1/PETG print guide](Antenna_V5_Reinforced/print_profiles/README_A1_PETG.md) and projects in `Antenna_V5_Reinforced/3MF_A1_PETG_0p4/`. Print calibration plate 00 before the full assembly. The other standalone 3MF files are earlier fitting experiments, not the main V5 print set.

STL/STEP/3MF assets and compact audit results are included. Python caches, regenerated `qa_cache/` geometry, and ZIP bundles duplicating the expanded folders are excluded from Git. The CAD guide lists the regeneration sequence; build the model before running validators that require `qa_cache/`.

## Tiếng Việt

**Bắt đầu từ [Antenna V5 Reinforced](Antenna_V5_Reinforced/README_START_HERE.md).** Đây là thiết kế cơ khí hiện hành cho cấu hình động cơ bước/TB6600, MT6701 và LD-1501MG.

| Thư mục | Vai trò |
| --- | --- |
| [`Antenna_V5_Reinforced/`](Antenna_V5_Reinforced/README_START_HERE.md) | Bản hiện hành: giá servo gia cố và gá cảm biến dạng mở |
| [`Antenna_V4_MT6701/`](Antenna_V4_MT6701/README_START_HERE.md) | Bản MT6701 trước đó; nguồn đối chiếu hình học cho V5 |
| [`Antenna_TheGioiIC_v3/`](Antenna_TheGioiIC_v3/README_START_HERE.md) | Nguyên mẫu cũ cùng tài liệu lắp ráp/mua linh kiện |
| `Antenna_TheGioiIC_v2/` | Nguyên mẫu trước, giữ để so sánh lịch sử |

Với V5, dùng [hướng dẫn in A1/PETG](Antenna_V5_Reinforced/print_profiles/README_A1_PETG.md) và các dự án trong `Antenna_V5_Reinforced/3MF_A1_PETG_0p4/`. In bàn hiệu chuẩn 00 trước khi in toàn bộ. Các file 3MF rời khác là thử nghiệm lắp ghép trước đây, không phải bộ in V5 chính.

Repo giữ dữ liệu STL/STEP/3MF và báo cáo kiểm tra gọn nhẹ. Cache Python, hình học `qa_cache/` có thể tái tạo và gói ZIP trùng với thư mục đã giải nén được loại khỏi Git. Hướng dẫn CAD có thứ tự tái tạo; cần build mô hình trước khi chạy các validator phụ thuộc `qa_cache/`.
