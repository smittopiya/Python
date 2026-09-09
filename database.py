
# database.py — The Veloria Grand Hotel Management System
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "veloria_hotel.db")


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self._create_tables()

    # ─── Schema ─────────────────────────────────────────────────────────────────
    def _create_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id        TEXT PRIMARY KEY,
                room_type      TEXT NOT NULL,
                price          REAL NOT NULL,
                capacity       INTEGER NOT NULL,
                extra_per_head REAL NOT NULL DEFAULT 0,
                photo_path     TEXT DEFAULT '',
                description    TEXT DEFAULT '',
                floor          INTEGER DEFAULT 1,
                status         TEXT DEFAULT 'Available',
                created_at     TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS clients (
                client_id       TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                gender          TEXT,
                contact         TEXT NOT NULL,
                address         TEXT DEFAULT '',
                city            TEXT DEFAULT '',
                state           TEXT DEFAULT '',
                country         TEXT DEFAULT 'India',
                id_proof_type   TEXT DEFAULT '',
                id_proof_number TEXT DEFAULT '',
                registered_date TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                client_id      TEXT,
                room_id        TEXT,
                check_in       TEXT NOT NULL,
                check_out      TEXT NOT NULL,
                adults         INTEGER DEFAULT 1,
                children       INTEGER DEFAULT 0,
                extra_persons  INTEGER DEFAULT 0,
                extra_charge   REAL DEFAULT 0,
                add_ons        TEXT DEFAULT '',
                meal_plan      TEXT DEFAULT 'No Meals',
                meal_quantity  INTEGER DEFAULT 1,
                meal_price     REAL DEFAULT 0,
                nights         INTEGER DEFAULT 1,
                base_amount    REAL DEFAULT 0,
                total_amount   REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'Pending',
                status         TEXT DEFAULT 'Confirmed',
                notes          TEXT DEFAULT '',
                created_at     TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (client_id) REFERENCES clients(client_id),
                FOREIGN KEY (room_id)   REFERENCES rooms(room_id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                payment_id     TEXT PRIMARY KEY,
                reservation_id TEXT,
                total_amount   REAL,
                paid_amount    REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'Pending',
                payment_method TEXT DEFAULT '',
                payment_date   TEXT DEFAULT '',
                invoice_number TEXT DEFAULT '',
                notes          TEXT DEFAULT '',
                FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
            );
        """)
        self.conn.commit()

    # ─── Room CRUD ───────────────────────────────────────────────────────────────
    def add_room(self, room_id, room_type, price, capacity, extra_per_head,
                 photo_path="", description="", floor=1):
        try:
            self.cursor.execute("""
                INSERT INTO rooms (room_id, room_type, price, capacity, extra_per_head,
                                   photo_path, description, floor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (room_id, room_type, float(price), int(capacity),
                  float(extra_per_head), photo_path, description, int(floor)))
            self.conn.commit()
            return True, "Room added successfully."
        except sqlite3.IntegrityError:
            return False, f"Room ID '{room_id}' already exists."
        except Exception as e:
            return False, str(e)

    def get_all_rooms(self):
        self.cursor.execute("SELECT * FROM rooms ORDER BY room_id")
        return self.cursor.fetchall()

    def get_room_by_id(self, room_id):
        self.cursor.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
        return self.cursor.fetchone()

    def get_available_rooms(self):
        self.cursor.execute("SELECT * FROM rooms WHERE status='Available' ORDER BY room_type, room_id")
        return self.cursor.fetchall()

    def get_rooms_available_today(self):
        """Rooms NOT in any active reservation covering today."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT * FROM rooms WHERE room_id NOT IN (
                SELECT DISTINCT room_id FROM reservations
                WHERE status IN ('Confirmed','Checked-in')
                AND check_in <= ? AND check_out > ?
            ) ORDER BY room_type, room_id
        """, (today, today))
        return self.cursor.fetchall()

    def get_rooms_booked_today(self):
        """Rooms in an active reservation that covers today."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT r.room_id, r.room_type, r.price, r.capacity, r.status,
                   c.name AS client_name, c.contact,
                   res.reservation_id, res.check_in, res.check_out,
                   res.adults, res.children, res.total_amount
            FROM rooms r
            JOIN reservations res ON r.room_id = res.room_id
            JOIN clients c ON res.client_id = c.client_id
            WHERE res.status IN ('Confirmed','Checked-in')
            AND res.check_in <= ? AND res.check_out > ?
            ORDER BY r.room_id
        """, (today, today))
        return self.cursor.fetchall()

    def get_all_rooms_with_today_status(self):
        """
        Returns all rooms with a dynamically computed 'today_status':
          - 'Occupied Today'  — has an active reservation covering today
          - 'Available Today' — no active reservation covering today
        Also includes guest name & reservation ID if occupied.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT
                r.room_id,
                r.room_type,
                r.price,
                r.capacity,
                r.extra_per_head,
                r.floor,
                r.description,
                CASE
                    WHEN res.reservation_id IS NOT NULL
                    THEN 'Occupied Today'
                    ELSE 'Available Today'
                END AS today_status,
                COALESCE(c.name, '')        AS guest_name,
                COALESCE(res.reservation_id,'') AS res_id,
                COALESCE(res.check_in,  '')  AS check_in,
                COALESCE(res.check_out, '')  AS check_out
            FROM rooms r
            LEFT JOIN reservations res
                ON r.room_id = res.room_id
                AND res.status IN ('Confirmed','Checked-in')
                AND res.check_in <= ? AND res.check_out > ?
            LEFT JOIN clients c ON res.client_id = c.client_id
            ORDER BY today_status DESC, r.room_type, r.room_id
        """, (today, today))
        return self.cursor.fetchall()


    def get_booked_rooms_with_info(self):
        self.cursor.execute("""
            SELECT r.room_id, r.room_type, r.price, r.capacity, r.status,
                   c.name AS client_name, c.contact,
                   res.reservation_id, res.check_in, res.check_out,
                   res.adults, res.children, res.total_amount
            FROM rooms r
            JOIN reservations res ON r.room_id = res.room_id
            JOIN clients c ON res.client_id = c.client_id
            WHERE r.status = 'Booked'
              AND res.status IN ('Confirmed','Checked-in')
            ORDER BY r.room_id
        """)
        return self.cursor.fetchall()

    def update_room(self, room_id, room_type, price, capacity, extra_per_head,
                    photo_path, description, floor):
        try:
            self.cursor.execute("""
                UPDATE rooms SET room_type=?, price=?, capacity=?, extra_per_head=?,
                photo_path=?, description=?, floor=? WHERE room_id=?
            """, (room_type, float(price), int(capacity), float(extra_per_head),
                  photo_path, description, int(floor), room_id))
            self.conn.commit()
            return True, "Room updated successfully."
        except Exception as e:
            return False, str(e)

    def update_room_status(self, room_id, status):
        self.cursor.execute("UPDATE rooms SET status=? WHERE room_id=?", (status, room_id))
        self.conn.commit()

    def delete_room(self, room_id):
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM reservations
                WHERE room_id=? AND status IN ('Confirmed','Checked-in')
            """, (room_id,))
            if self.cursor.fetchone()[0] > 0:
                return False, "Cannot delete: room has active reservations."
            self.cursor.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
            self.conn.commit()
            return True, "Room deleted successfully."
        except Exception as e:
            return False, str(e)

    def search_rooms(self, query):
        q = f"%{query}%"
        self.cursor.execute("""
            SELECT * FROM rooms
            WHERE room_id LIKE ? OR room_type LIKE ? OR status LIKE ? OR description LIKE ?
            ORDER BY room_id
        """, (q, q, q, q))
        return self.cursor.fetchall()

    def get_room_ids(self):
        self.cursor.execute("SELECT room_id FROM rooms ORDER BY room_id")
        return [r[0] for r in self.cursor.fetchall()]

    def get_available_rooms_for_dates(self, check_in, check_out, exclude_res_id=None):
        """Rooms not booked during the given date range."""
        if exclude_res_id:
            self.cursor.execute("""
                SELECT * FROM rooms WHERE room_id NOT IN (
                    SELECT DISTINCT room_id FROM reservations
                    WHERE status IN ('Confirmed','Checked-in')
                    AND reservation_id != ?
                    AND check_in < ? AND check_out > ?
                ) ORDER BY room_type, room_id
            """, (exclude_res_id, check_out, check_in))
        else:
            self.cursor.execute("""
                SELECT * FROM rooms WHERE room_id NOT IN (
                    SELECT DISTINCT room_id FROM reservations
                    WHERE status IN ('Confirmed','Checked-in')
                    AND check_in < ? AND check_out > ?
                ) ORDER BY room_type, room_id
            """, (check_out, check_in))
        return self.cursor.fetchall()

    # ─── Client CRUD ─────────────────────────────────────────────────────────────
    def check_id_proof_unique(self, id_proof_type, id_proof_number, exclude_client_id=None):
        """Returns True if the id_proof_number is unique (not used by another client)."""
        if exclude_client_id:
            self.cursor.execute("""
                SELECT COUNT(*) FROM clients
                WHERE id_proof_number=? AND client_id != ?
            """, (id_proof_number.strip().upper(), exclude_client_id))
        else:
            self.cursor.execute("""
                SELECT COUNT(*) FROM clients WHERE id_proof_number=?
            """, (id_proof_number.strip().upper(),))
        return self.cursor.fetchone()[0] == 0

    def add_client(self, client_id, name, gender, contact, address, city,
                   state, country, id_proof_type, id_proof_number):
        try:
            self.cursor.execute("""
                INSERT INTO clients (client_id, name, gender, contact, address, city,
                                     state, country, id_proof_type, id_proof_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, name, gender, contact, address, city,
                  state, country, id_proof_type, id_proof_number))
            self.conn.commit()
            return True, "Client registered successfully."
        except sqlite3.IntegrityError:
            return False, f"Client ID '{client_id}' already exists."
        except Exception as e:
            return False, str(e)

    def get_all_clients(self):
        self.cursor.execute("SELECT * FROM clients ORDER BY name")
        return self.cursor.fetchall()

    def get_client_by_id(self, client_id):
        self.cursor.execute("SELECT * FROM clients WHERE client_id=?", (client_id,))
        return self.cursor.fetchone()

    def update_client(self, client_id, name, gender, contact, address, city,
                      state, country, id_proof_type, id_proof_number):
        try:
            self.cursor.execute("""
                UPDATE clients SET name=?, gender=?, contact=?, address=?, city=?,
                state=?, country=?, id_proof_type=?, id_proof_number=?
                WHERE client_id=?
            """, (name, gender, contact, address, city,
                  state, country, id_proof_type, id_proof_number, client_id))
            self.conn.commit()
            return True, "Client updated successfully."
        except Exception as e:
            return False, str(e)

    def delete_client(self, client_id):
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM reservations
                WHERE client_id=? AND status IN ('Confirmed','Checked-in')
            """, (client_id,))
            if self.cursor.fetchone()[0] > 0:
                return False, "Cannot delete: client has active reservations."
            self.cursor.execute("DELETE FROM clients WHERE client_id=?", (client_id,))
            self.conn.commit()
            return True, "Client deleted successfully."
        except Exception as e:
            return False, str(e)

    def get_client_ids_names(self):
        self.cursor.execute("SELECT client_id, name FROM clients ORDER BY name")
        return self.cursor.fetchall()

    # ─── Reservation CRUD ────────────────────────────────────────────────────────
    def add_reservation(self, res_id, client_id, room_id, check_in, check_out,
                        adults, children, extra_persons, extra_charge,
                        add_ons, meal_plan, meal_quantity, meal_price,
                        nights, base_amount, total_amount, notes=""):
        try:
            self.cursor.execute("""
                INSERT INTO reservations (reservation_id, client_id, room_id,
                check_in, check_out, adults, children, extra_persons, extra_charge,
                add_ons, meal_plan, meal_quantity, meal_price, nights,
                base_amount, total_amount, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (res_id, client_id, room_id, check_in, check_out,
                  adults, children, extra_persons, extra_charge,
                  add_ons, meal_plan, meal_quantity, meal_price,
                  nights, base_amount, total_amount, notes))
            self.update_room_status(room_id, "Booked")
            self.conn.commit()
            return True, f"Reservation {res_id} confirmed."
        except sqlite3.IntegrityError:
            return False, f"Reservation ID '{res_id}' already exists."
        except Exception as e:
            return False, str(e)

    def get_all_reservations(self):
        self.cursor.execute("""
            SELECT res.*, c.name AS client_name, r.room_type
            FROM reservations res
            JOIN clients c ON res.client_id = c.client_id
            JOIN rooms r ON res.room_id = r.room_id
            ORDER BY res.created_at DESC
        """)
        return self.cursor.fetchall()

    def get_reservation_detail(self, res_id):
        self.cursor.execute("""
            SELECT res.*,
                   c.name AS client_name, c.contact, c.address, c.city,
                   c.state, c.country, c.id_proof_type, c.id_proof_number,
                   r.room_type, r.price AS room_price, r.capacity
            FROM reservations res
            JOIN clients c ON res.client_id = c.client_id
            JOIN rooms r ON res.room_id = r.room_id
            WHERE res.reservation_id = ?
        """, (res_id,))
        return self.cursor.fetchone()

    def get_all_reservations_for_billing(self):
        self.cursor.execute("""
            SELECT res.*, c.name AS client_name, c.contact, r.room_type
            FROM reservations res
            JOIN clients c ON res.client_id = c.client_id
            JOIN rooms r ON res.room_id = r.room_id
            ORDER BY res.payment_status, res.check_out
        """)
        return self.cursor.fetchall()

    def update_reservation_payment(self, res_id, payment_status, method=""):
        try:
            self.cursor.execute("""
                UPDATE reservations SET payment_status=? WHERE reservation_id=?
            """, (payment_status, res_id))
            if payment_status == "Paid":
                self.cursor.execute(
                    "SELECT room_id, check_out FROM reservations WHERE reservation_id=?",
                    (res_id,))
                row = self.cursor.fetchone()
                if row:
                    today = datetime.now().strftime("%Y-%m-%d")
                    if row[1] <= today:
                        self.update_room_status(row[0], "Available")
            self.conn.commit()
            return True, "Payment status updated."
        except Exception as e:
            return False, str(e)

    def cancel_reservation(self, res_id):
        try:
            self.cursor.execute(
                "SELECT room_id FROM reservations WHERE reservation_id=?", (res_id,))
            row = self.cursor.fetchone()
            if row:
                self.update_room_status(row[0], "Available")
            self.cursor.execute(
                "UPDATE reservations SET status='Cancelled' WHERE reservation_id=?",
                (res_id,))
            self.conn.commit()
            return True, "Reservation cancelled."
        except Exception as e:
            return False, str(e)

    def update_reservation(self, res_id, room_id, check_in, check_out,
                           adults, children, extra_persons, extra_charge,
                           add_ons, meal_plan, meal_quantity, meal_price,
                           nights, base_amount, total_amount, notes=""):
        """Update all editable fields of an existing reservation."""
        try:
            self.cursor.execute("""
                UPDATE reservations SET
                    room_id=?, check_in=?, check_out=?,
                    adults=?, children=?, extra_persons=?, extra_charge=?,
                    add_ons=?, meal_plan=?, meal_quantity=?, meal_price=?,
                    nights=?, base_amount=?, total_amount=?, notes=?
                WHERE reservation_id=?
            """, (room_id, check_in, check_out,
                  adults, children, extra_persons, extra_charge,
                  add_ons, meal_plan, meal_quantity, meal_price,
                  nights, base_amount, total_amount, notes,
                  res_id))
            self.conn.commit()
            return True, f"Reservation {res_id} updated successfully."
        except Exception as e:
            return False, str(e)

    def get_reservation_by_id(self, res_id):
        """Fetch a single reservation with room and client details."""
        self.cursor.execute("""
            SELECT res.*,
                   c.name AS client_name,
                   r.room_type, r.price AS room_price, r.capacity,
                   r.extra_per_head, r.description AS amenities, r.photo_path
            FROM reservations res
            JOIN clients c ON res.client_id = c.client_id
            JOIN rooms r   ON res.room_id   = r.room_id
            WHERE res.reservation_id = ?
        """, (res_id,))
        return self.cursor.fetchone()


    # ─── Dashboard Stats ─────────────────────────────────────────────────────────
    def get_dashboard_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        c = self.cursor
        stats = {}

        c.execute("SELECT COUNT(*) FROM rooms")
        stats["total_rooms"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM rooms WHERE status='Available'")
        stats["available_rooms"] = c.fetchone()[0]

        c.execute("""
            SELECT COALESCE(SUM(adults+children),0) FROM reservations
            WHERE check_in<=? AND check_out>? AND status IN ('Confirmed','Checked-in')
        """, (today, today))
        stats["active_guests"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM clients")
        stats["registered_clients"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM reservations WHERE payment_status='Pending' AND status != 'Cancelled'")
        stats["pending_payments"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM reservations WHERE status != 'Cancelled'")
        stats["total_bookings"] = c.fetchone()[0]

        c.execute("SELECT COALESCE(SUM(total_amount),0) FROM reservations WHERE payment_status='Paid'")
        stats["total_revenue"] = c.fetchone()[0]

        return stats

    # ─── Analytics ───────────────────────────────────────────────────────────────
    def get_reservations_by_room_chart(self):
        """Simple totals for backwards compat (not used by chart1 anymore)."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT r.room_id, COUNT(res.reservation_id) AS cnt
            FROM rooms r
            LEFT JOIN reservations res ON r.room_id = res.room_id
                AND res.check_out >= ? AND res.status IN ('Confirmed','Checked-in')
            GROUP BY r.room_id ORDER BY r.room_id
        """, (today,))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows], [r[1] for r in rows]

    def get_reservations_by_room_grouped(self):
        """
        Returns per-room counts split into three groups:
          - current:  active/checked-in today
          - upcoming: confirmed but check-in is in the future
          - completed: past reservations (check_out <= today, not cancelled)
        Returns (room_ids, current_counts, upcoming_counts, completed_counts)
        All rooms are included even if count = 0.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT
                r.room_id,
                SUM(CASE
                    WHEN res.status IN ('Confirmed','Checked-in')
                         AND res.check_in <= ? AND res.check_out > ?
                    THEN 1 ELSE 0
                END) AS current_cnt,
                SUM(CASE
                    WHEN res.status = 'Confirmed'
                         AND res.check_in > ?
                    THEN 1 ELSE 0
                END) AS upcoming_cnt,
                SUM(CASE
                    WHEN res.status NOT IN ('Cancelled')
                         AND res.check_out <= ?
                    THEN 1 ELSE 0
                END) AS completed_cnt
            FROM rooms r
            LEFT JOIN reservations res ON r.room_id = res.room_id
            GROUP BY r.room_id
            ORDER BY r.room_id
        """, (today, today, today, today))
        rows = self.cursor.fetchall()
        room_ids   = [r[0] for r in rows]
        current    = [r[1] or 0 for r in rows]
        upcoming   = [r[2] or 0 for r in rows]
        completed  = [r[3] or 0 for r in rows]
        return room_ids, current, upcoming, completed

    def get_room_type_distribution(self):
        self.cursor.execute("""
            SELECT room_type, COUNT(*) FROM rooms GROUP BY room_type
        """)
        rows = self.cursor.fetchall()
        return [r[0] for r in rows], [r[1] for r in rows]

    def get_occupied_vs_available_by_type(self):
        self.cursor.execute("""
            SELECT room_type,
                   SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) AS avail,
                   SUM(CASE WHEN status='Booked'    THEN 1 ELSE 0 END) AS booked
            FROM rooms GROUP BY room_type
        """)
        rows = self.cursor.fetchall()
        types   = [r[0] for r in rows]
        avail   = [r[1] for r in rows]
        booked  = [r[2] for r in rows]
        return types, avail, booked

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
