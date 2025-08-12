import json
from datetime import datetime
from colorama import Fore, Style, init
from prettytable import PrettyTable
import random
import getpass
import os
from cryptography.fernet import Fernet
import speech_recognition as sr
import pyttsx3
from fpdf import FPDF
import markdown

# Initialize colorama
init(autoreset=True)

class JournalEntry:
    """Class to represent a single journal entry
    
    Attributes:
        title (str): Title of the journal entry
        content (str): Main content of the entry
        mood (str): Current mood (e.g., happy, sad)
        mood_rating (int): Mood rating from 1-10
        tags (list): List of tags for categorization
        completed_tasks (list): List of completed tasks
        forgettable_thing (str): Something the user wants to forget
        date (str): Creation timestamp
    """
    def __init__(self, title, content, mood, mood_rating, tags=None, 
                 completed_tasks=None, forgettable_thing=None):
        self.title = title
        self.content = content
        self.mood = mood
        self.mood_rating = mood_rating
        self.tags = tags if tags else []
        self.completed_tasks = completed_tasks if completed_tasks else []
        self.forgettable_thing = forgettable_thing
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def display(self, show_full=False):
        """Display the journal entry
        
        Args:
            show_full (bool): Whether to show full content or just summary
        """
        print(Fore.YELLOW + f"\n{'='*50}")
        print(Fore.CYAN + f"Title: {self.title}")
        print(Fore.GREEN + f"Date: {self.date}")
        print(Fore.MAGENTA + f"Mood: {self.mood} (Rating: {self.mood_rating}/10)")
        
        # Mood feedback
        if self.mood_rating < 4:
            print(Fore.RED + "You seem down. Remember: This too shall pass!")
        elif self.mood_rating > 7:
            print(Fore.GREEN + "Great mood! Keep the positivity going!")
        
        if show_full:
            print(Fore.BLUE + "\nContent:")
            print(Fore.WHITE + self.content)
            
            if self.tags:
                print(Fore.CYAN + "\nTags: " + ", ".join(self.tags))
                
            if self.completed_tasks:
                print(Fore.GREEN + "\nCompleted Tasks:")
                for i, task in enumerate(self.completed_tasks, 1):
                    print(f"{i}. {task}")
                    
            if self.forgettable_thing:
                print(Fore.RED + "\nThing to Forget: " + self.forgettable_thing)
        else:
            preview = (self.content[:50] + '...') if len(self.content) > 50 else self.content
            print(Fore.BLUE + "\nPreview: " + preview)
            
        print(Fore.YELLOW + f"{'='*50}\n")
        
    def to_dict(self):
        """Convert entry to dictionary for serialization"""
        return {
            'title': self.title,
            'content': self.content,
            'mood': self.mood,
            'mood_rating': self.mood_rating,
            'tags': self.tags,
            'completed_tasks': self.completed_tasks,
            'forgettable_thing': self.forgettable_thing,
            'date': self.date
        }

class JournalManager:
    """Class to manage journal entries with file operations
    
    Attributes:
        filename (str): Path to journal data file
        entries (list): List of JournalEntry objects
        key (bytes): Encryption key for secure storage
        current_user (str): Currently logged in user
    """
    def __init__(self, username):
        """Initialize journal manager for a specific user"""
        self.username = username
        self.filename = f"journal_{username}.json"
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        self.entries = []
        self.load_entries()
        
    def _get_or_create_key(self):
        """Get or create encryption key for user"""
        key_file = f"key_{self.username}.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
            
    def _encrypt(self, data):
        """Encrypt data before saving"""
        return self.cipher.encrypt(data.encode()).decode()
        
    def _decrypt(self, data):
        """Decrypt loaded data"""
        return self.cipher.decrypt(data.encode()).decode()
        
    def load_entries(self):
        """Load entries from encrypted JSON file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as file:
                    encrypted_data = file.read()
                    if encrypted_data:
                        decrypted_data = self._decrypt(encrypted_data)
                        data = json.loads(decrypted_data)
                        self.entries = [JournalEntry(**entry) for entry in data]
                    else:
                        self.entries = []
        except (json.JSONDecodeError, Exception) as e:
            print(Fore.RED + f"Error loading journal: {str(e)}")
            self.entries = []
            
    def save_entries(self):
        """Save entries to encrypted JSON file"""
        try:
            data = json.dumps([entry.to_dict() for entry in self.entries])
            encrypted_data = self._encrypt(data)
            with open(self.filename, 'w') as file:
                file.write(encrypted_data)
                
            # Create backup
            backup_file = f"backup_{self.filename}"
            with open(backup_file, 'w') as file:
                file.write(encrypted_data)
        except Exception as e:
            print(Fore.RED + f"Error saving journal: {str(e)}")
            
    def add_entry(self, entry):
        """Add a new entry"""
        self.entries.append(entry)
        self.save_entries()
        
    def edit_entry(self, index, new_entry):
        """Edit an existing entry"""
        if 0 <= index < len(self.entries):
            self.entries[index] = new_entry
            self.save_entries()
            return True
        return False
        
    def delete_entry(self, index):
        """Delete an entry"""
        if 0 <= index < len(self.entries):
            del self.entries[index]
            self.save_entries()
            return True
        return False
        
    def view_all_entries(self, show_full=False):
        """View all entries in table format"""
        if not self.entries:
            print(Fore.RED + "No entries found!")
            return
            
        table = PrettyTable()
        table.field_names = [
            Fore.CYAN + "#", 
            Fore.GREEN + "Date", 
            Fore.BLUE + "Title", 
            Fore.MAGENTA + "Mood", 
            Fore.YELLOW + "Rating"
        ]
        table.align = "l"
        
        for i, entry in enumerate(self.entries, 1):
            table.add_row([
                i,
                entry.date,
                entry.title,
                entry.mood,
                f"{entry.mood_rating}/10"
            ])
            
        print(table)
        
        if show_full and self.entries:
            try:
                choice = int(input(Fore.YELLOW + "Enter entry number to view (0 to cancel): ")) - 1
                if 0 <= choice < len(self.entries):
                    self.entries[choice].display(show_full=True)
            except ValueError:
                print(Fore.RED + "Invalid input!")
                
    def search_entries(self):
        """Search entries by mood or date"""
        print(Fore.CYAN + "\nSearch Options:")
        print("1. By Mood")
        print("2. By Date Range")
        print("3. By Tag")
        choice = input(Fore.YELLOW + "Enter search option (1-3): ")
        
        if choice == '1':
            mood = input(Fore.MAGENTA + "Enter mood to search for: ")
            found = [entry for entry in self.entries if mood.lower() in entry.mood.lower()]
        elif choice == '2':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
                found = [
                    entry for entry in self.entries 
                    if start <= datetime.strptime(entry.date[:10], "%Y-%m-%d") <= end
                ]
            except ValueError:
                print(Fore.RED + "Invalid date format! Use YYYY-MM-DD")
                return
        elif choice == '3':
            tag = input("Enter tag to search for: ")
            found = [entry for entry in self.entries if tag.lower() in [t.lower() for t in entry.tags]]
        else:
            print(Fore.RED + "Invalid choice!")
            return
            
        if not found:
            print(Fore.RED + "No matching entries found!")
            return
            
        table = PrettyTable()
        table.field_names = [Fore.CYAN + "Date", Fore.GREEN + "Title", Fore.MAGENTA + "Mood"]
        table.align = "l"
        
        for entry in found:
            table.add_row([entry.date, entry.title, entry.mood])
            
        print(table)
        
    def export_to_pdf(self):
        """Export all entries to PDF"""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt=f"Journal for {self.username}", ln=1, align='C')
        
        for entry in self.entries:
            pdf.cell(200, 10, txt=f"Date: {entry.date}", ln=1)
            pdf.cell(200, 10, txt=f"Title: {entry.title}", ln=1)
            pdf.cell(200, 10, txt=f"Mood: {entry.mood} ({entry.mood_rating}/10)", ln=1)
            pdf.multi_cell(0, 10, txt=f"Content:\n{entry.content}")
            
            if entry.tags:
                pdf.cell(0, 10, txt=f"Tags: {', '.join(entry.tags)}", ln=1)
                
            if entry.completed_tasks:
                pdf.cell(0, 10, txt="Completed Tasks:", ln=1)
                for task in entry.completed_tasks:
                    pdf.cell(0, 10, txt=f"- {task}", ln=1)
                    
            pdf.cell(0, 10, txt="-"*50, ln=1)
            
        pdf_file = f"journal_{self.username}.pdf"
        pdf.output(pdf_file)
        print(Fore.GREEN + f"Journal exported to {pdf_file}!")
        
    def export_to_markdown(self):
        """Export all entries to Markdown"""
        md_content = f"# Journal for {self.username}\n\n"
        
        for entry in self.entries:
            md_content += f"## {entry.title}\n"
            md_content += f"**Date**: {entry.date}\n"
            md_content += f"**Mood**: {entry.mood} ({entry.mood_rating}/10)\n\n"
            md_content += f"{entry.content}\n\n"
            
            if entry.tags:
                md_content += f"**Tags**: {', '.join(entry.tags)}\n\n"
                
            if entry.completed_tasks:
                md_content += "**Completed Tasks**:\n"
                for task in entry.completed_tasks:
                    md_content += f"- {task}\n"
                md_content += "\n"
                
            md_content += "---\n\n"
            
        md_file = f"journal_{self.username}.md"
        with open(md_file, 'w') as f:
            f.write(md_content)
            
        print(Fore.GREEN + f"Journal exported to {md_file}!")
        
    def voice_entry(self):
        """Create entry using voice input"""
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        print(Fore.CYAN + "Speak your journal entry after the beep...")
        
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source)
                print(Fore.YELLOW + "Listening... (say 'stop' to finish)")
                audio = recognizer.listen(source, phrase_time_limit=120)
                
            content = recognizer.recognize_google(audio)
            print(Fore.GREEN + "\nYou said: " + content)
            
            if content.lower().strip() == 'stop':
                print(Fore.RED + "Voice entry cancelled!")
                return
                
            title = input(Fore.GREEN + "Enter title for this entry: ")
            mood = input(Fore.MAGENTA + "Enter your mood: ")
            mood_rating = self._get_valid_rating()
            
            entry = JournalEntry(
                title=title,
                content=content,
                mood=mood,
                mood_rating=mood_rating
            )
            
            self.add_entry(entry)
            print(Fore.GREEN + "Voice entry saved successfully!")
            
        except sr.UnknownValueError:
            print(Fore.RED + "Could not understand audio")
        except sr.RequestError:
            print(Fore.RED + "Could not request results from speech service")
        except Exception as e:
            print(Fore.RED + f"Error: {str(e)}")
            
    def _get_valid_rating(self):
        """Get a valid mood rating from 1-10"""
        while True:
            try:
                rating = int(input(Fore.YELLOW + "Rate your mood (1-10): "))
                if 1 <= rating <= 10:
                    return rating
                print(Fore.RED + "Rating must be between 1-10!")
            except ValueError:
                print(Fore.RED + "Please enter a number!")
                
    def get_random_quote(self):
        """Get random inspirational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Life is what happens when you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "In the middle of every difficulty lies opportunity. - Albert Einstein",
            "You miss 100% of the shots you don't take. - Wayne Gretzky"
        ]
        return random.choice(quotes)

def authenticate_user():
    """Handle user authentication"""
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.YELLOW + "PERSONAL JOURNAL LOGIN")
    print(Fore.CYAN + "="*50)
    
    while True:
        print("\n1. Login")
        print("2. Create new user")
        print("3. Exit")
        
        choice = input(Fore.YELLOW + "Enter choice (1-3): ")
        
        if choice == '1':
            username = input(Fore.GREEN + "Username: ")
            password = getpass.getpass(Fore.BLUE + "Password: ")
            
            # Simple authentication - in real app, use proper hashing
            if os.path.exists(f"user_{username}.txt"):
                with open(f"user_{username}.txt", 'r') as f:
                    stored_password = f.read().strip()
                if password == stored_password:
                    return username
                print(Fore.RED + "Invalid password!")
            else:
                print(Fore.RED + "User not found!")
                
        elif choice == '2':
            username = input(Fore.GREEN + "Choose username: ")
            if os.path.exists(f"user_{username}.txt"):
                print(Fore.RED + "Username already exists!")
                continue
                
            password = getpass.getpass(Fore.BLUE + "Choose password: ")
            confirm = getpass.getpass(Fore.BLUE + "Confirm password: ")
            
            if password == confirm:
                with open(f"user_{username}.txt", 'w') as f:
                    f.write(password)
                print(Fore.GREEN + "User created successfully!")
                return username
            else:
                print(Fore.RED + "Passwords don't match!")
                
        elif choice == '3':
            return None
        else:
            print(Fore.RED + "Invalid choice!")

def create_new_entry(journal_manager):
    """Create a new journal entry with validation"""
    print(Fore.CYAN + "\n--- Create New Journal Entry ---")
    print(Fore.YELLOW + journal_manager.get_random_quote())
    
    title = input(Fore.GREEN + "Enter title: ")
    while not title.strip():
        print(Fore.RED + "Title cannot be empty!")
        title = input(Fore.GREEN + "Enter title: ")
    
    content = input(Fore.BLUE + "Enter your thoughts: ")
    while not content.strip():
        print(Fore.RED + "Content cannot be empty!")
        content = input(Fore.BLUE + "Enter your thoughts: ")
    
    mood = input(Fore.MAGENTA + "Enter your current mood (e.g., happy, sad, anxious): ")
    mood_rating = journal_manager._get_valid_rating()
    
    print(Fore.CYAN + "\nAdditional Options (press enter to skip):")
    tags = input(Fore.YELLOW + "Enter tags (comma separated): ")
    tags = [tag.strip() for tag in tags.split(',')] if tags else []
    
    tasks = input(Fore.GREEN + "Enter completed tasks (comma separated): ")
    tasks = [task.strip() for task in tasks.split(',')] if tasks else []
    
    forgettable = input(Fore.RED + "Enter something you'd like to forget: ")
    
    entry = JournalEntry(
        title=title,
        content=content,
        mood=mood,
        mood_rating=mood_rating,
        tags=tags,
        completed_tasks=tasks,
        forgettable_thing=forgettable if forgettable else None
    )
    
    journal_manager.add_entry(entry)
    print(Fore.GREEN + "\nEntry saved successfully!")

def edit_existing_entry(journal_manager):
    """Edit an existing journal entry"""
    if not journal_manager.entries:
        print(Fore.RED + "No entries to edit!")
        return
        
    journal_manager.view_all_entries()
    try:
        choice = int(input(Fore.YELLOW + "Enter entry number to edit (0 to cancel): ")) - 1
        if choice == -1:
            return
        if 0 <= choice < len(journal_manager.entries):
            old_entry = journal_manager.entries[choice]
            print(Fore.CYAN + "\nEditing Entry:")
            old_entry.display(show_full=True)
            
            print(Fore.YELLOW + "\nEnter new values (press enter to keep current):")
            
            title = input(Fore.GREEN + f"Title [{old_entry.title}]: ") or old_entry.title
            content = input(Fore.BLUE + f"Content [{old_entry.content[:20]}...]: ") or old_entry.content
            mood = input(Fore.MAGENTA + f"Mood [{old_entry.mood}]: ") or old_entry.mood
            
            # For rating, we need special handling to ensure validity
            while True:
                rating_input = input(Fore.YELLOW + f"Mood Rating [{old_entry.mood_rating}]: ")
                if not rating_input:
                    mood_rating = old_entry.mood_rating
                    break
                try:
                    mood_rating = int(rating_input)
                    if 1 <= mood_rating <= 10:
                        break
                    print(Fore.RED + "Rating must be between 1-10!")
                except ValueError:
                    print(Fore.RED + "Please enter a number!")
            
            tags = input(Fore.CYAN + f"Tags [{', '.join(old_entry.tags)}]: ")
            tags = [tag.strip() for tag in tags.split(',')] if tags else old_entry.tags
            
            tasks = input(Fore.GREEN + f"Tasks [{', '.join(old_entry.completed_tasks)}]: ")
            tasks = [task.strip() for task in tasks.split(',')] if tasks else old_entry.completed_tasks
            
            forgettable = input(Fore.RED + f"Forgettable [{old_entry.forgettable_thing}]: ") 
            forgettable = forgettable if forgettable else old_entry.forgettable_thing
            
            new_entry = JournalEntry(
                title=title,
                content=content,
                mood=mood,
                mood_rating=mood_rating,
                tags=tags,
                completed_tasks=tasks,
                forgettable_thing=forgettable
            )
            
            if journal_manager.edit_entry(choice, new_entry):
                print(Fore.GREEN + "Entry updated successfully!")
            else:
                print(Fore.RED + "Failed to update entry!")
        else:
            print(Fore.RED + "Invalid entry number!")
    except ValueError:
        print(Fore.RED + "Please enter a valid number!")

def delete_entry(journal_manager):
    """Delete a journal entry"""
    if not journal_manager.entries:
        print(Fore.RED + "No entries to delete!")
        return
        
    journal_manager.view_all_entries()
    try:
        choice = int(input(Fore.YELLOW + "Enter entry number to delete (0 to cancel): ")) - 1
        if choice == -1:
            return
        if 0 <= choice < len(journal_manager.entries):
            journal_manager.entries[choice].display(show_full=True)
            confirm = input(Fore.RED + "Are you sure you want to delete this entry? (y/n): ")
            if confirm.lower() == 'y':
                if journal_manager.delete_entry(choice):
                    print(Fore.GREEN + "Entry deleted successfully!")
                else:
                    print(Fore.RED + "Failed to delete entry!")
    except ValueError:
        print(Fore.RED + "Please enter a valid number!")

def main_menu(journal_manager):
    """Display main menu and handle user choices"""
    while True:
        print(Fore.YELLOW + "\n" + "="*50)
        print(Fore.CYAN + f"PERSONAL JOURNAL - {journal_manager.username.upper()}")
        print(Fore.YELLOW + "="*50)
        print(Fore.GREEN + "1. Write a new journal entry")
        print(Fore.BLUE + "2. View all entries")
        print(Fore.MAGENTA + "3. Search entries")
        print(Fore.CYAN + "4. Edit an entry")
        print(Fore.RED + "5. Delete an entry")
        print(Fore.YELLOW + "6. Voice entry (speak your thoughts)")
        print(Fore.GREEN + "7. Export to PDF")
        print(Fore.BLUE + "8. Export to Markdown")
        print(Fore.RED + "9. Logout")
        
        choice = input(Fore.YELLOW + "\nEnter your choice (1-9): ")
        
        if choice == '1':
            create_new_entry(journal_manager)
        elif choice == '2':
            journal_manager.view_all_entries(show_full=True)
        elif choice == '3':
            journal_manager.search_entries()
        elif choice == '4':
            edit_existing_entry(journal_manager)
        elif choice == '5':
            delete_entry(journal_manager)
        elif choice == '6':
            journal_manager.voice_entry()
        elif choice == '7':
            journal_manager.export_to_pdf()
        elif choice == '8':
            journal_manager.export_to_markdown()
        elif choice == '9':
            print(Fore.YELLOW + "Logging out...")
            break
        else:
            print(Fore.RED + "Invalid choice! Please enter a number between 1-9.")

def main():
    """Main application entry point"""
    # Check for required libraries
    try:
        import colorama
        import prettytable
        import cryptography
        import speech_recognition
        import pyttsx3
        import fpdf
    except ImportError as e:
        print(Fore.RED + f"Error: Required library not found - {e.name}")
        print(Fore.YELLOW + "Please install with: pip install colorama prettytable cryptography SpeechRecognition pyttsx3 fpdf")
        return
        
    # Main application loop
    while True:
        username = authenticate_user()
        if not username:
            print(Fore.YELLOW + "Goodbye!")
            break
            
        journal_manager = JournalManager(username)
        main_menu(journal_manager)

if __name__ == "__main__":
    main()