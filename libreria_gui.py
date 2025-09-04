import sqlite3 as sq
import pandas as pd
import tkinter as tk
from tkinter import messagebox
import requests
from tkinter import ttk

class ManagerApp:
    def __init__(self, root):
        self.root = root
        ### Titolo ###
        self.root.title("Libreria Casa Fini")
        self.root.geometry("400x300+100+100")
        ### Connesione al DB ###
        self.db_path = 'libri.db'
        self.conn = self.connection()
        if self.conn:
            self.create_table()
        else:
            messagebox.showerror("Errore", "Impossibile connettersi al DB")
            self.root.destroy()
            return
        ### Crea Finestra ###
        self.set_up_gui()

    def connection(self):
        '''
        Crea la connesione al DB
        '''
        conn = None 
        try:
            conn = sq.connect(self.db_path)
        except sq.Error as e:
            print(e)
        
        return conn

    def create_table(self):
        '''
        Crea la tabella nel DB
        '''
        try:
            c = self.conn.cursor()
            c.execute('''
                    CREATE TABLE Libri(
                    Titolo VARCHAR(255),
                    Autore VARCHAR(255),
                    Editore VARCHAR(255),
                    Data_pub VARCHAR(10),
                    Descrizione VARCHAR(255),
                    Pagine INT,
                    ISBN BIGINT PRIMARY KEY,
                    aut_id INT  )
                    ''')
            
            c.execute('''
                    CREATE TABLE Autori(
                    id INTEGER PRIMARY KEY,
                    nome VARCHAR(255))
                    ''')
        except sq.Error as e:
            print(e)

    def insert_author(self, author_name):
        """
        Inserisce un autore nel database se non esiste e restituisce il suo ID.
        """
        # 1. Controlla se l'autore esiste già
        sql_check = "SELECT id FROM autori WHERE nome = ?"
        cur = self.conn.cursor()
        cur.execute(sql_check, (author_name,))
        row = cur.fetchone()

        if row:
            # L'autore esiste, restituisci il suo ID
            return row[0]
        else:
            # L'autore non esiste, inseriscilo e restituisci il nuovo ID
            sql_insert = "INSERT INTO autori(nome) VALUES(?)"
            cur.execute(sql_insert, (author_name,))
            self.conn.commit()
            return cur.lastrowid


    def insert_book(self,book):
        '''
        Inserisce un libro nel DB
        '''
        try:
            c = self.conn.cursor()
            
            author_id = self.insert_author(book[1])
            book.append(author_id)
            sql = '''
                    INSERT INTO Libri (Titolo, Autore, Editore, Data_pub, Descrizione, Pagine, ISBN, aut_id) VALUES
                    (?,?,?,?,?,?,?,?)
                    '''
            c.execute(sql,book)

            self.conn.commit()
        except sq.Error as e:
            print(e)

    def search(self, isbn):
        """
        Cerca libro nel DB
        """
        cur = self.conn.cursor()
        cur.execute(""" SELECT * FROM lIBRI WHERE ISBN = ? """, (isbn,))
        return cur.fetchone() is None  

    def get_book_info(self,isbn):
        """
        Recupera i dati del codice ISBN da Google Libri
        """
        url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            ### controlla se ci sono risultati ###
            if data['totalItems']>0:
                    volume_info = data['items'][0]['volumeInfo']

                    ### estrae le informazioni ###
                    titolo = volume_info.get('title', 'N/A')
                    autore = volume_info.get('authors', ['N/A'])
                    editore = volume_info.get('publisher', 'N/A')
                    data_pub = volume_info.get('publishedDate', 'N/A')
                    descrizione = volume_info.get('description', 'N/A')
                    pag = volume_info.get('pageCount', 'N/A')
                    ### restituisce un dizionario con i dati
                    return {
                        'Titolo':titolo,
                        'Autore':str(', '.join(autore)),
                        'Editore':editore,
                        'Data_pub':data_pub,
                        'Descrizione':descrizione,
                        'Pagine':pag,
                        'ISBN':isbn
                    }
            else:
                    print('Libro non trovato')
                    return None

        except requests.exceptions.RequestException as e:
            print(e)
            return None
    
    def add_book_from_gui(self):
        """
        Funzione per l'aggiunta di libri da GUI
        """
        isbn = self.entry_isbn.get()
        if not isbn:
            messagebox.showwarning("Attenzione", "Inserisci codice ISBN.")
            return
        if not self.search(isbn):
            messagebox.showinfo("Avviso", f"Il libro con ISBN {isbn} è già presente nel DB")
            self.entry_isbn.delete(0, tk.END)
            return
        book_data = self.get_book_info(isbn)
        if book_data:
            self.insert_book(list(book_data.values()))
            messagebox.showinfo("Successo", f"Il libro '{book_data['Titolo']}' è stato aggiunto correttamente")
            # Cancella il contenuto del campo di testo 
            self.entry_isbn.delete(0, tk.END)
        else:
            messagebox.showerror("Errore", "Nessun liro trovato per questo ISBN")
            self.entry_isbn.delete(0, tk.END)

    def set_up_gui(self):
        """
        Configurazione Interfaccia utente
        """
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10)
        label_isbn = ttk.Label(self.root, text="Inserisci ISBN:")
        label_isbn.pack(pady=5)

        self.entry_isbn = ttk.Entry(self.root)
        self.entry_isbn.pack(pady=5)
        self.entry_isbn.bind('<Return>', lambda event=None: self.add_book_from_gui())

        button_add = ttk.Button(self.root, text="Aggiungi Libro", command = self.add_book_from_gui)
        button_add.pack(pady=10)


if __name__ == '__main__':
    root = tk.Tk()
    app = ManagerApp(root)
    root.mainloop()