import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import sqlite3

# Định nghĩa đường dẫn tới file database
URL_DATABASE = "./assets/data/books.db"

# Hàm khởi tạo database
def init_db():
    # Kết nối tới file cơ sở dữ liệu books.db (tạo mới nếu chưa có)
    conn = sqlite3.connect(URL_DATABASE)
    
    # Tạo cursor để thực thi các lệnh SQL
    c = conn.cursor()
    
    # Tạo bảng books nếu chưa tồn tại, với các cột:
    # - id: Khóa chính, tự động tăng (1, 2, 3...)
    # - title: Tên sách, kiểu TEXT, không được để trống
    # - author: Tác giả, kiểu TEXT, không được để trống
    # - year: Năm xuất bản, kiểu INTEGER
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  author TEXT NOT NULL,
                  year INTEGER)''')
    
    # Lưu các thay đổi (tạo bảng) vào file books.db
    conn.commit()
    
    # Đóng kết nối để giải phóng tài nguyên
    conn.close()

# Hàm đọc dữ liệu từ database và hiển thị lên Treeview
def refresh_tree(view: ttk.Treeview):
    # Xóa dữ liệu cũ trên Treeview
    for item in view.get_children():
        view.delete(item)
    
    # Kết nối tới database
    conn = sqlite3.connect(URL_DATABASE)
    c = conn.cursor()
    
    # Lấy tất cả dữ liệu từ bảng books
    c.execute("SELECT * FROM books")
    books = c.fetchall()  # Trả về list các bản ghi
    
    for index, book in enumerate(books, start=1):  # Bắt đầu STT từ 1
        book_id = book[0]  # Lấy id từ database
        display_data = (index, book[1], book[2], book[3])  # (STT, title, author, year)
        view.insert("", "end", values=display_data, tags=(book_id,))  # Lưu id vào tags
    
    # Đóng kết nối
    conn.close()

# Hàm thêm một cuốn sách
def add_book(book_entry: tk.Entry, author_entry: tk.Entry, year_entry: tk.Entry, view: ttk.Treeview):
    # Kết nối tới database
    conn = sqlite3.connect(URL_DATABASE)  # Đảm bảo URL_DATABASE đã được định nghĩa
    c = conn.cursor()

    # Lấy dữ liệu từ các Entry và kiểm tra không bỏ trống
    book_data = get_data_entry(book_entry, "Tên sách không thể để trống")
    author_data = get_data_entry(author_entry, "Tên tác giả không thể để trống")
    year_data = get_data_entry(year_entry, "Năm sản xuất không thể để trống")  # Sửa thông báo lỗi cho đúng

    # Kiểm tra dữ liệu hợp lệ
    if book_data and author_data and year_data:
        try:
            year_data = int(year_data)  # Thử chuyển year thành số nguyên
        except ValueError:
            messagebox.showerror("Lỗi", "Năm sản xuất phải là số nguyên!")
            conn.close()  # Đóng kết nối trước khi thoát
            return
        
        # Kiểm tra xem sách đã tồn tại trong database chưa
        c.execute("SELECT COUNT(*) FROM books WHERE title = ? AND author = ? AND year = ?",
                  (book_data, author_data, year_data))
        count = c.fetchone()[0]  # Số lượng bản ghi trùng lặp
        
        if count > 0:  # Nếu đã có sách trùng
            messagebox.showwarning("Cảnh báo", "Sách này đã tồn tại trong database!")
            conn.close()
            return
        
        # Thêm dữ liệu vào bảng books
        c.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", (book_data, author_data, year_data))
        conn.commit()  # Lưu thay đổi vào database
        

        # Thông báo thành công và làm mới Treeview
        messagebox.showinfo("Thành công", "Đã thêm sách vào database!")
        refresh_tree(view)  # Làm mới Treeview để hiển thị dữ liệu mới
        conn.close()  # Đóng kết nối

        # Xóa các ô Entry sau khi thêm
        book_entry.delete(0, tk.END)  # Xóa nội dung ô nhập liệu Tên sách
        author_entry.delete(0, tk.END)  # Xóa nội dung ô nhập liệu Tác giả
        year_entry.delete(0, tk.END)  # Xóa nội dung ô nhập liệu Năm xuất bản
    else:
        conn.close()  # Đóng kết nối nếu có lỗi nhập liệu

# Hàm lấy dữ liệu Entry
def get_data_entry(entry: tk.Entry, mess: str):
    data = entry.get().strip()  # Lấy dữ liệu từ ô nhập liệu
    if not data:  # Kiểm tra nếu dữ liệu trống
        messagebox.showerror("Lỗi", mess)  # Hiển thị thông báo lỗi với nội dung mess
        return None  # Trả về None nếu dữ liệu trống
    return data  # Trả về dữ liệu nếu hợp lệ

# Hàm xóa một cuốn sách
def delete_book(view: ttk.Treeview):
    # Kết nối tới database
    conn = sqlite3.connect(URL_DATABASE)  # Đảm bảo URL_DATABASE đã được định nghĩa
    c = conn.cursor()

    selected_item = view.selection()  # Lấy danh sách các hàng được chọn trong Treeview
    if not selected_item:  # Kiểm tra xem có hàng nào được chọn không
        messagebox.showerror("Lỗi", "Vui lòng chọn một sách để xóa!")  # Hiển thị lỗi nếu không có hàng nào được chọn
        return
    # Lấy dữ liệu của hàng được chọn (để lấy ID)
    book_id = view.item(selected_item[0], "tags")[0]  # Lấy id từ tags
    # Xác nhận trước khi xóa
    if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sách này không?"):  # Hiển thị hộp thoại xác nhận
        return  # Thoát nếu người dùng chọn "No"
    
    c.execute("DELETE FROM books WHERE id = ?", (book_id,))  # Xóa bản ghi theo ID
    conn.commit()  # Lưu thay đổi vào database
    conn.close()  # Đóng kết nối

    # Làm mới Treeview
    refresh_tree(view)  # Cập nhật Treeview để phản ánh việc xóa
    messagebox.showinfo("Thành công", "Đã xóa sách!")  # Thông báo xóa thành công

# Hàm sửa sách 
def update_book(book_entry: tk.Entry, author_entry: tk.Entry, year_entry: tk.Entry, view: ttk.Treeview):
    # Lấy hàng được chọn trong Treeview
    selected_item = view.selection()  # Lấy danh sách các hàng được chọn
    if not selected_item:  # Kiểm tra xem có hàng nào được chọn không
        messagebox.showerror("Lỗi", "Vui lòng chọn một sách để sửa!")  # Hiển thị lỗi nếu không có hàng nào được chọn
        return
    
  
    # Lấy id từ tags của hàng được chọn
    book_id = view.item(selected_item[0], "tags")[0]  # Lấy id từ tags

   

    # Lấy dữ liệu từ các ô Entry
    new_title = book_entry.get().strip()  # Tên sách mới, loại bỏ khoảng trắng thừa
    new_author = author_entry.get().strip()  # Tác giả mới, loại bỏ khoảng trắng thừa
    new_year = year_entry.get().strip()  # Năm mới, loại bỏ khoảng trắng thừa

    # Lấy dữ liệu hiện tại từ database để so sánh
    conn = sqlite3.connect(URL_DATABASE)  # Kết nối tới database
    c = conn.cursor()
    c.execute("SELECT title, author, year FROM books WHERE id = ?", (book_id,))  # Lấy dữ liệu hiện tại của sách
    current_data = c.fetchone()  # (title, author, year) hiện tại trong database
    if not current_data:  # Kiểm tra xem sách có tồn tại trong database không
        messagebox.showerror("Lỗi", "Không tìm thấy sách trong database!")  # Hiển thị lỗi nếu không tìm thấy
        conn.close()  # Đóng kết nối
        return

    # Nếu ô trống, giữ nguyên giá trị cũ
    updated_title = new_title if new_title else current_data[0]  # Giữ nguyên tên sách cũ nếu ô trống
    updated_author = new_author if new_author else current_data[1]  # Giữ nguyên tác giả cũ nếu ô trống
    
    # Kiểm tra và xử lý năm
    if new_year:  # Nếu ô năm không trống
        try:
            updated_year = int(new_year)  # Chuyển năm thành số nguyên
        except ValueError:
            messagebox.showerror("Lỗi", "Năm sản xuất phải là số nguyên!")  # Hiển thị lỗi nếu năm không phải số nguyên
            conn.close()  # Đóng kết nối
            return
    else:
        updated_year = current_data[2]  # Giữ nguyên năm cũ nếu ô trống

    # Kiểm tra xem có thay đổi nào không
    if (updated_title == current_data[0] and 
        updated_author == current_data[1] and 
        updated_year == current_data[2]):  # So sánh dữ liệu mới và cũ
        messagebox.showinfo("Thông báo", "Không có thay đổi để cập nhật!")  # Thông báo nếu không có thay đổi
        conn.close()  # Đóng kết nối
        return

    # Cập nhật dữ liệu trong database
    c.execute("UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?",
              (updated_title, updated_author, updated_year, book_id))  # Cập nhật bản ghi
    conn.commit()  # Lưu thay đổi
    conn.close()  # Đóng kết nối

    # Làm mới Treeview
    refresh_tree(view)  # Cập nhật Treeview để hiển thị dữ liệu mới

    # Xóa các ô Entry sau khi sửa
    book_entry.delete(0, tk.END)  # Xóa nội dung ô nhập liệu Tên sách
    author_entry.delete(0, tk.END)  # Xóa nội dung ô nhập liệu Tác giả
    year_entry.delete(0, tk.END)  # Xóa nội dung ô nhập liệu Năm xuất bản

    messagebox.showinfo("Thành công", "Đã cập nhật sách!")  # Thông báo cập nhật thành công

# Hàm xử lý sự kiện nhấp chuột để bỏ chọn hàng trong Treeview
def on_treeview_click(event:dict, view:ttk.Entry):
    # Lấy vùng được nhấp
    region = view.identify_region(event.x, event.y)
    
    # Nếu nhấp vào vùng trống (không phải hàng hoặc tiêu đề), bỏ chọn tất cả
    if region != "cell" and region != "heading":
        view.selection_remove(view.selection())

# Hàm thoát app
def exit_app(root: tk.Tk):
    if messagebox.askyesno("Thoát", "Bạn có chắc muốn thoát không?"):  # Hiển thị hộp thoại xác nhận thoát
        root.quit()  # Thoát ứng dụng nếu người dùng chọn "Yes"

# Hàm hiển thị cửa sổ hướng dẫn
def show_help_window(root: tk.Tk):
    help_window = tk.Toplevel(root)  # Tạo cửa sổ con (Toplevel) để hiển thị hướng dẫn
    help_window.title("Hướng Dẫn Sử Dụng")  # Đặt tiêu đề cho cửa sổ hướng dẫn
    help_window.geometry("500x400")  # Đặt kích thước cho cửa sổ hướng dẫn

    # Tạo frame để chứa Text widget và Scrollbar
    frame = tk.Frame(help_window)
    frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Tạo thanh cuộn
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    # Tạo Text widget để hiển thị nội dung hướng dẫn
    help_text_widget = tk.Text(
        frame,
        wrap="word",  # Tự động xuống dòng theo từ
        font=("Arial", 10),  # Font chữ và kích thước
        yscrollcommand=scrollbar.set,  # Kết nối với thanh cuộn
        height=20,  # Chiều cao của Text widget
        width=60  # Chiều rộng của Text widget
    )
    help_text_widget.pack(side="left", fill="both", expand=True)

    # Kết nối thanh cuộn với Text widget
    scrollbar.config(command=help_text_widget.yview)

    # Nội dung hướng dẫn
    help_content = (
        "HƯỚNG DẪN SỬ DỤNG ỨNG DỤNG QUẢN LÝ SÁCH\n\n"
        "1. Thêm Sách:\n"
        "   - Nhập thông tin sách (Tên sách, Tên tác giả, Năm xuất bản) vào các ô nhập liệu.\n"
        "   - Nhấn nút 'Thêm' để thêm sách vào database.\n"
        "   - Lưu ý: Sách trùng (cùng tên, tác giả, năm) sẽ không được thêm.\n\n"
        "2. Xóa Sách:\n"
        "   - Chọn một sách trong bảng (Treeview).\n"
        "   - Nhấn nút 'Xóa' và xác nhận để xóa sách khỏi database.\n\n"
        "3. Sửa Sách:\n"
        "   - Chọn một sách trong bảng (Treeview).\n"
        "   - Nhập thông tin mới vào các ô nhập liệu (bỏ trống để giữ nguyên giá trị cũ).\n"
        "   - Nhấn nút 'Sửa' để cập nhật thông tin sách.\n\n"
        "4. Mở File CSV (File > Open):\n"
        "   - Chọn 'Open' từ menu 'File' để mở file CSV.\n"
        "   - File CSV phải có các cột: title, author, year.\n"
        "   - Dữ liệu từ file sẽ được thêm vào database (bỏ qua các sách trùng lặp).\n\n"
        "5. Lưu Dữ Liệu Ra File CSV (File > Save):\n"
        "   - Chọn 'Save' từ menu 'File' để lưu dữ liệu hiện tại ra file CSV.\n"
        "   - Chọn nơi lưu và đặt tên file, dữ liệu sẽ được lưu với định dạng: title,author,year.\n\n"
    )
    
    # Thêm nội dung vào Text widget
    help_text_widget.insert("end", help_content)
    help_text_widget.config(state="disabled")  # Không cho phép chỉnh sửa nội dung

    # Thêm nút Đóng để đóng cửa sổ hướng dẫn
    close_button = tk.Button(help_window, text="Đóng", command=help_window.destroy)
    close_button.pack(pady=5)

# Hàm mở file CSV và thêm dữ liệu vào database (không dùng thư viện csv)
def open_csv_file(view: ttk.Treeview):
    # Mở hộp thoại để chọn file CSV
    file_path = filedialog.askopenfilename(
        title="Chọn file CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    
    if not file_path:  # Nếu người dùng không chọn file (nhấn Cancel)
        return
    
    try:
        # Kết nối tới database
        conn = sqlite3.connect(URL_DATABASE)
        c = conn.cursor()
        
        # Đọc file CSV thủ công
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()  # Đọc tất cả các dòng trong file
            
            if not lines:  # Kiểm tra nếu file trống
                messagebox.showerror("Lỗi", "File CSV trống!")
                conn.close()
                return
            
            # Xử lý dòng tiêu đề (header)
            header = lines[0].strip().split(',')  # Tách dòng đầu tiên thành list các cột
            header = [col.strip() for col in header]  # Loại bỏ khoảng trắng thừa
            
            # Kiểm tra xem file CSV có các cột cần thiết không
            required_columns = {'title', 'author', 'year'}
            if not required_columns.issubset(header):
                messagebox.showerror("Lỗi", "File CSV phải có các cột: title, author, year!")
                conn.close()
                return
            
            # Lấy chỉ số của các cột
            title_idx = header.index('title')
            author_idx = header.index('author')
            year_idx = header.index('year')
            
            # Xử lý các dòng dữ liệu
            for line in lines[1:]:  # Bỏ qua dòng tiêu đề
                data = line.strip().split(',')  # Tách dòng thành list các giá trị
                if len(data) < len(header):  # Kiểm tra nếu dòng không đủ cột
                    messagebox.showwarning("Cảnh báo", f"Bỏ qua dòng: {line.strip()} - Dữ liệu không đủ cột!")
                    continue
                
                title = data[title_idx].strip()
                author = data[author_idx].strip()
                year = data[year_idx].strip()
                
                # Kiểm tra dữ liệu hợp lệ
                if not title or not author:
                    messagebox.showwarning("Cảnh báo", f"Bỏ qua dòng: {line.strip()} - Tên sách và tác giả không được để trống!")
                    continue
                
                try:
                    year = int(year) if year else None  # Chuyển year thành số nguyên, nếu trống thì để None
                except ValueError:
                    messagebox.showwarning("Cảnh báo", f"Bỏ qua dòng: {line.strip()} - Năm phải là số nguyên!")
                    continue
                
                # Kiểm tra xem sách đã tồn tại trong database chưa
                c.execute("SELECT COUNT(*) FROM books WHERE title = ? AND author = ? AND year = ?",
                          (title, author, year))
                count = c.fetchone()[0]  # Số lượng bản ghi trùng lặp
                
                if count > 0:  # Nếu đã có sách trùng
                    messagebox.showwarning("Cảnh báo", f"Bỏ qua dòng: {line.strip()} - Sách này đã tồn tại trong database!")
                    continue  # Bỏ qua dòng này và tiếp tục với dòng tiếp theo
                
                # Thêm vào database
                c.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", (title, author, year))
        
        conn.commit()  # Lưu thay đổi vào database
        conn.close()  # Đóng kết nối
        
        # Làm mới Treeview
        refresh_tree(view)
        messagebox.showinfo("Thành công", "Đã nhập dữ liệu từ file CSV vào database!")
    
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc file CSV: {str(e)}")
        if 'conn' in locals(): # Kiểm tra xem đã đóng kết nối chưa
            conn.close()

# Hàm lưu dữ liệu từ database ra file CSV (không dùng thư viện csv)
def save_to_csv():
    # Mở hộp thoại để chọn nơi lưu file CSV
    file_path = filedialog.asksaveasfilename(
        title="Lưu file CSV",
        defaultextension=".csv",  # Tự động thêm đuôi .csv nếu người dùng không nhập
        filetypes=[("CSV files", "*.csv")]
    )
    
    if not file_path:  # Nếu người dùng không chọn file (nhấn Cancel)
        return
    
    try:
        # Kết nối tới database
        conn = sqlite3.connect(URL_DATABASE)
        c = conn.cursor()
        
        # Lấy tất cả dữ liệu từ bảng books
        c.execute("SELECT title, author, year FROM books")
        books = c.fetchall()  # Trả về list các bản ghi (title, author, year)
        
        # Đóng kết nối
        conn.close()
        
        # Ghi dữ liệu ra file CSV
        with open(file_path, 'w', encoding='utf-8') as file:
            # Ghi dòng tiêu đề (header)
            header = "title,author,year\n"
            file.write(header)
            
            # Ghi từng dòng dữ liệu
            for book in books:
                title = str(book[0])  # Chuyển thành string để tránh lỗi
                author = str(book[1])
                year = str(book[2]) if book[2] is not None else ""  # Nếu year là None, để trống
                # Ghi dòng dữ liệu, các giá trị cách nhau bằng dấu phẩy
                line = f"{title},{author},{year}\n"
                file.write(line)
        
        messagebox.showinfo("Thành công", "Đã lưu dữ liệu vào file CSV!")
    
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể lưu file CSV: {str(e)}")

def main():
    init_db()  # Khởi tạo database
    root = tk.Tk()  # Tạo cửa sổ chính với tiêu đề và kích thước 600x400
    root.title("Quản Lý Sách")  # Gán title ứng dụng
    root.geometry("600x400")  # Chọn kích thước geometry
    root.resizable(False, False) # Ngăn thay đổi kích thước của sổ
    icon = tk.PhotoImage(file='./assets/images/book_icon.png')  # Tải icon cho app từ file PNG
    root.iconphoto(True, icon)  # Thêm icon vào app, True:  áp dụng cho tất cả cửa sổ hiện tại

    menu_bar = tk.Menu(root)  # Tạo thanh menu
    root.config(menu=menu_bar)  # Gắn menu_bar vào cửa sổ root, biến nó thành thanh menu chính của ứng dụng
    # Thêm các thành phần của menu_bar
    file_menu = tk.Menu(menu_bar, tearoff=0)  # Tạo thanh file_menu, không cho phép nó tách ra làm cửa sổ riêng
    menu_bar.add_cascade(label="File", menu=file_menu)  # Thêm một menu thả xuống (dropdown menu) có tên "File" vào thanh Menu Bar
    file_menu.add_cascade(label="Open", command=lambda: open_csv_file(view))  # Thêm chức năng Open file csv để đọc dữ liệu đã lưu
    file_menu.add_cascade(label="Save", command=lambda: save_to_csv())  # Thêm chức năng Save file csv để lưu dữ liệu hiện có thành file csv
    file_menu.add_separator()  # Tạo đường phân cách trong menu File
    file_menu.add_cascade(label="Exit", command=lambda: exit_app(root))  # Thêm chức năng Exit để thoát ứng dụng
    menu_bar.add_cascade(label="Help", command=lambda: show_help_window(root))  # Thêm chức năng Help để hiển thị cửa sổ hướng dẫn

    frame_input = tk.Frame(root)  # Tạo frame chứa các ô nhập liệu
    frame_input.pack(pady=10)  # Đặt frame_input vào cửa sổ root, cho nó khoảng cách là 10px với các phần khác
    # Thêm các thành phần vào frame_input
    # Tạo ô nhập tên sách
    tk.Label(frame_input, text="Tên sách").grid(row=0, column=0, padx=5, pady=5)  # Tạo nhãn "Tên sách" tại dòng 0, cột 0
    book_entry = tk.Entry(frame_input, width=30)  # Tạo ô nhập liệu cho Tên sách, rộng 30 ký tự
    book_entry.grid(row=0, column=1, padx=5, pady=5)  # Đặt ô nhập liệu tại dòng 0, cột 1

    # Tạo ô nhập tên tác giả
    tk.Label(frame_input, text="Tên tác giả").grid(row=1, column=0, padx=5, pady=5)  # Tạo nhãn "Tên tác giả" tại dòng 1, cột 0
    author_entry = tk.Entry(frame_input, width=30)  # Tạo ô nhập liệu cho Tên tác giả, rộng 30 ký tự
    author_entry.grid(row=1, column=1, padx=5, pady=5)  # Đặt ô nhập liệu tại dòng 1, cột 1

    # Tạo ô nhận năm xuất bản
    tk.Label(frame_input, text="Năm xuất bản").grid(row=2, column=0, padx=5, pady=5)  # Tạo nhãn "Năm xuất bản" tại dòng 2, cột 0
    year_entry = tk.Entry(frame_input, width=30)  # Tạo ô nhập liệu cho Năm xuất bản, rộng 30 ký tự
    year_entry.grid(row=2, column=1, padx=5, pady=5)  # Đặt ô nhập liệu tại dòng 2, cột 1

    # Tạo thanh chứa các nút
    frame_buttons = tk.Frame(root)  # Tạo Frame chứa các nút Thêm, Xóa, Sửa
    frame_buttons.pack(pady=10)  # Đặt Frame vào cửa sổ root với khoảng cách trên/dưới 10px
    add_button = tk.Button(frame_buttons, text="Thêm", 
                           command=lambda: add_book(book_entry, author_entry, year_entry, view))  # Tạo nút Thêm và gắn lệnh add_book
    add_button.grid(row=0, column=0, padx=5, pady=5)  # Đặt nút Thêm tại dòng 0, cột 0
    remove_button = tk.Button(frame_buttons, text="Xóa", 
                            command=lambda: delete_book(view))  # Tạo nút Xóa và gắn lệnh delete_book
    remove_button.grid(row=0, column=1, padx=5, pady=5)  # Đặt nút Xóa tại dòng 0, cột 1
    update_button = tk.Button(frame_buttons, text="Sửa",
                              command=lambda: update_book(book_entry, author_entry, year_entry, view))  # Tạo nút Sửa và gắn lệnh update_book
    update_button.grid(row=0, column=2, padx=5, pady=5)  # Đặt nút Sửa tại dòng 0, cột 2
    
    # Tạo bảng show dữ liệu
    view = ttk.Treeview(root, column=('id', 'book_name', 'author_name', 'year'), show="headings")  # Tạo Treeview với 4 cột
    view.heading("id", text="STT")  # Đặt tiêu đề cho cột id là "STT"
    view.heading("book_name", text="Tên sách")  # Đặt tiêu đề cho cột book_name là "Tên sách"
    view.heading("author_name", text="Tên tác giả")  # Đặt tiêu đề cho cột author_name là "Tên tác giả"
    view.heading("year", text="Năm xuất bản")  # Đặt tiêu đề cho cột year là "Năm xuất bản"

    view.column("id", width=50)  # Đặt chiều rộng cột id là 50px
    view.column("book_name", width=200)  # Đặt chiều rộng cột book_name là 200px
    view.column("author_name", width=100)  # Đặt chiều rộng cột author_name là 100px
    view.column("year", width=100)  # Đặt chiều rộng cột year là 100px
    view.pack(pady=10)  # Đặt Treeview vào cửa sổ root với khoảng cách trên/dưới 10px

    # Gắn sự kiện nhấp chuột vào Treeview, truyền view qua lambda
    view.bind("<Button-1>", lambda event: on_treeview_click(event, view))

    refresh_tree(view)  # Làm mới Treeview để hiển thị dữ liệu ban đầu
    root.mainloop()  # Chạy vòng lặp chính của ứng dụng Tkinter

if __name__ == '__main__':
    main()  # Gọi hàm main() để chạy ứng dụng