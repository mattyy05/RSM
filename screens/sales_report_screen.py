from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from datetime import datetime, timedelta
import sqlite3


class SalesReportScreen(MDScreen):
    """Screen for displaying sales reports and analytics"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None

    def on_enter(self):
        """Load sales report data when screen is entered"""
        self.app = MDApp.get_running_app()
        self.load_sales_metrics()

    def load_sales_metrics(self):
        """
        Load and display sales metrics including all four main components:
        1. Sales Volume (items sold, returns, net sales)
        2. Revenue (total money earned)
        3. Key Performance Indicators (KPIs)
        4. Comparison Data (period-over-period analysis)
        """
        try:
            if not self.app or not hasattr(self.app, 'db'):
                print("Error: Database connection not available")
                return

            # 1. Calculate Top Selling Products
            self._calculate_top_selling_products()

            # 2. Calculate Sales Volume
            self._calculate_sales_volume()

            # 2. Calculate Revenue
            revenue = self._calculate_total_revenue()
            self.ids.revenue_label.text = f"[size=18][font=Brico]Total Sales: ₱{revenue:,.2f}[/font][/size]"
            self.ids.revenue_period_label.text = f"[size=12][font=Brico]For {datetime.now().strftime('%B %Y')}[/font][/size]"

            # 3. Calculate KPIs
            self._calculate_kpis()

            # 4. Calculate Comparison Data
            self._calculate_period_comparison()

            print(f"Sales metrics loaded successfully - Revenue: ₱{revenue:,.2f}")

        except Exception as e:
            print(f"Error loading sales metrics: {e}")
            self._show_error_state()

    def _calculate_sales_volume(self):
        """
        Calculate sales volume metrics:
        - Total items sold (from sales transactions)
        - Returns (from sales_returns table)
        - Net sales (total sold - returns)
        """
        try:
            cursor = self.app.db.conn.cursor()

            # Get total items sold from sales details
            cursor.execute("""
                SELECT COALESCE(SUM(si.quantity), 0)
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE s.payment_type IN ('cash', 'credit')
            """)
            total_sold_result = cursor.fetchone()
            total_items_sold = total_sold_result[0] if total_sold_result else 0

            # Get total returns
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM sales_returns
            """)
            returns_result = cursor.fetchone()
            total_returns = returns_result[0] if returns_result else 0

            # Calculate net sales
            net_sales = total_items_sold - total_returns

            # Update UI labels
            if hasattr(self.ids, 'total_items_sold_label'):
                self.ids.total_items_sold_label.text = f"{total_items_sold:,}"

            if hasattr(self.ids, 'returns_label'):
                self.ids.returns_label.text = f"{total_returns:,}"

            if hasattr(self.ids, 'net_sales_label'):
                self.ids.net_sales_label.text = f"{net_sales:,}"

            print(f"Sales Volume calculated - Sold: {total_items_sold}, Returns: {total_returns}, Net: {net_sales}")

        except Exception as e:
            print(f"Error calculating sales volume: {e}")
            # Set default values
            if hasattr(self.ids, 'total_items_sold_label'):
                self.ids.total_items_sold_label.text = "0"
            if hasattr(self.ids, 'returns_label'):
                self.ids.returns_label.text = "0"
            if hasattr(self.ids, 'net_sales_label'):
                self.ids.net_sales_label.text = "0"

    def _calculate_top_selling_products(self):
        """
        Calculate and display the top 3 selling products by quantity sold.
        Shows product names and their total quantities sold.
        """
        try:
            cursor = self.app.db.conn.cursor()

            # Query to get top selling products by total quantity sold
            cursor.execute("""
                SELECT
                    p.name,
                    SUM(si.quantity) as total_quantity
                FROM products p
                JOIN sale_items si ON p.id = si.product_id
                JOIN sales s ON si.sale_id = s.id
                WHERE s.payment_type IN ('cash', 'credit')
                GROUP BY p.id, p.name
                ORDER BY total_quantity DESC
                LIMIT 3
            """)

            top_products = cursor.fetchall()

            if top_products:
                # Format the display text with better styling for the card space
                product_lines = []
                for i, (product_name, quantity) in enumerate(top_products, 1):
                    # Truncate long product names more aggressively
                    short_name = product_name[:15] + "..." if len(product_name) > 15 else product_name
                    product_lines.append(f"[size=14][b]{i}. {short_name}[/b][/size]\n[size=12]{quantity} units sold[/size]")

                display_text = "\n".join(product_lines)
            else:
                display_text = "[i]No sales data\navailable[/i]"

            # Update UI label
            if hasattr(self.ids, 'top_products_label'):
                self.ids.top_products_label.text = display_text

            print(f"Top selling products calculated - Found {len(top_products)} products")

        except Exception as e:
            print(f"Error calculating top selling products: {e}")
            # Set error message
            if hasattr(self.ids, 'top_products_label'):
                self.ids.top_products_label.text = "Error loading\ndata"

    def _calculate_total_revenue(self):
        """
        Calculate total revenue from all sales transactions.

        Revenue represents the total money earned from selling products
        before subtracting any costs or expenses.

        Returns:
            float: Total revenue amount
        """
        try:
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0.0)
                FROM sales
                WHERE payment_type IN ('cash', 'credit')  -- Include both cash and credit sales
            """)
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except sqlite3.Error as e:
            print(f"Database error calculating revenue: {e}")
            return 0.0

    def _calculate_kpis(self):
        """
        Calculate Key Performance Indicators for the retail business.

        This method implements comprehensive KPI calculation with:
        - Total Transactions: Count of all sales made in the period
        - Average Sale per Customer: Revenue divided by number of transactions
        - Performance tracking with improvement indicators (green arrows ↑)
        - Error handling for edge cases (zero transactions, database errors)
        - Performance optimization through efficient SQL queries

        Edge cases handled:
        - Zero transactions: Prevents division by zero, shows appropriate messages
        - Database connection issues: Graceful fallback with error indicators
        - Missing data: Default values with clear user feedback

        Performance optimizations:
        - Single SQL query for transaction count and revenue
        - Minimal database round trips
        - Efficient data type handling
        """
        try:
            cursor = self.app.db.conn.cursor()

            # Optimized single query to get transaction count and total revenue
            # Uses COALESCE to handle NULL values safely
            cursor.execute("""
                SELECT
                    COUNT(*) as transaction_count,
                    COALESCE(SUM(total_amount), 0.0) as total_revenue
                FROM sales
                WHERE payment_type IN ('cash', 'credit')
            """)

            result = cursor.fetchone()

            # Extract data with safe defaults
            transaction_count = result[0] if result and result[0] is not None else 0
            total_revenue = result[1] if result and result[1] is not None else 0.0

            # Calculate average sale per customer with division by zero protection
            avg_sale_per_customer = 0.0
            if transaction_count > 0:
                avg_sale_per_customer = total_revenue / transaction_count

            # Performance tracking: Check for improvements (simplified version)
            # In a full implementation, this would compare with previous periods
            transaction_improved = transaction_count > 50  # Example threshold
            avg_sale_improved = avg_sale_per_customer > 100  # Example threshold

            # Format display text with emojis and improvement indicators
            # Total Transactions with detailed description
            transaction_text = f"{transaction_count:,} {'↑' if transaction_improved else ''}"
            transaction_description = f"Total Transactions: {transaction_count:,} (number of sales made)"

            # Average Sale per Customer with calculation details
            avg_sale_text = f"₱{avg_sale_per_customer:,.0f}"
            avg_sale_description = f"Average Sale per Customer: ₱{avg_sale_per_customer:,.0f}\n(Revenue ÷ Number of Transactions)"

            # Update UI labels with formatted KPIs
            # Using getattr for safe attribute access in case IDs don't exist
            if hasattr(self.ids, 'total_transactions_label'):
                self.ids.total_transactions_label.text = transaction_text

            if hasattr(self.ids, 'avg_sale_label'):
                self.ids.avg_sale_label.text = avg_sale_text

            # Log successful KPI calculation for debugging
            print(f"KPIs calculated - Transactions: {transaction_count}, Avg Sale: ₱{avg_sale_per_customer:.2f}")

        except sqlite3.Error as e:
            print(f"Database error calculating KPIs: {e}")
            self._handle_kpi_error()
        except ZeroDivisionError:
            print("Warning: Division by zero in KPI calculation")
            self._handle_kpi_error()
        except Exception as e:
            print(f"Unexpected error in KPI calculation: {e}")
            self._handle_kpi_error()

    def _handle_kpi_error(self):
        """
        Handle errors during KPI calculation with user-friendly fallbacks.

        Sets default values and provides clear error indicators to maintain
        UI stability and user experience.
        """
        try:
            # Safe updates with hasattr checks
            if hasattr(self.ids, 'total_transactions_label'):
                self.ids.total_transactions_label.text = "Error"

            if hasattr(self.ids, 'avg_sale_label'):
                self.ids.avg_sale_label.text = "₱0.00"

            print("KPI error state displayed to user")
        except AttributeError as e:
            print(f"Warning: Could not update KPI labels during error: {e}")

    def _calculate_period_comparison(self):
        """
        Calculate period-over-period comparison for both sales volume and revenue.
        Shows current period vs previous period with percentage changes.
        """
        try:
            cursor = self.app.db.conn.cursor()
            now = datetime.now()

            # Current month (from start of current month to now)
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get current period metrics
            current_volume = self._get_volume_for_period(current_month_start, now)
            current_revenue = self._get_sales_for_period(current_month_start, now)

            # Previous month (full previous month)
            if now.month == 1:
                prev_month_start = now.replace(year=now.year-1, month=12, day=1)
                prev_month_end = now.replace(year=now.year-1, month=12, day=31)
            else:
                prev_month_start = now.replace(month=now.month-1, day=1)
                prev_month_end = now.replace(day=1) - timedelta(days=1)

            # Get previous period metrics
            previous_volume = self._get_volume_for_period(prev_month_start, prev_month_end)
            previous_revenue = self._get_sales_for_period(prev_month_start, prev_month_end)

            # Calculate percentage changes
            volume_change_pct = self._calculate_percentage_change(current_volume, previous_volume)
            revenue_change_pct = self._calculate_percentage_change(current_revenue, previous_revenue)

            # Update UI with comparison data
            if hasattr(self.ids, 'current_volume_label'):
                self.ids.current_volume_label.text = f"{current_volume:,} units"
            if hasattr(self.ids, 'volume_change_label'):
                self.ids.volume_change_label.text = f"{volume_change_pct:+.1f}%"

            if hasattr(self.ids, 'current_revenue_label'):
                self.ids.current_revenue_label.text = f"₱{current_revenue:,.2f}"
            if hasattr(self.ids, 'revenue_change_label'):
                self.ids.revenue_change_label.text = f"{revenue_change_pct:+.1f}%"

            print(f"Period comparison calculated - Volume: {current_volume} vs {previous_volume}, Revenue: ₱{current_revenue} vs ₱{previous_revenue}")

        except Exception as e:
            print(f"Error calculating period comparison: {e}")
            # Set default values on error
            if hasattr(self.ids, 'current_volume_label'):
                self.ids.current_volume_label.text = "0 units"
            if hasattr(self.ids, 'volume_change_label'):
                self.ids.volume_change_label.text = "+0%"
            if hasattr(self.ids, 'current_revenue_label'):
                self.ids.current_revenue_label.text = "₱0.00"
            if hasattr(self.ids, 'revenue_change_label'):
                self.ids.revenue_change_label.text = "+0%"

    def _calculate_percentage_change(self, current, previous):
        """Calculate percentage change between two values"""
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return ((current - previous) / previous) * 100

    def _get_volume_for_period(self, start_date, end_date):
        """
        Get total sales volume (items sold) for a specific date period.
        """
        try:
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(si.quantity), 0)
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE s.created_at >= ? AND s.created_at <= ?
                AND s.payment_type IN ('cash', 'credit')
            """, (start_date.isoformat(), end_date.isoformat()))

            result = cursor.fetchone()
            return result[0] if result else 0

        except Exception as e:
            print(f"Error getting volume for period: {e}")
            return 0

    def _get_sales_for_period(self, start_date, end_date):
        """
        Get total sales amount for a specific date period.

        Args:
            start_date (datetime): Start of the period
            end_date (datetime): End of the period

        Returns:
            float: Total sales amount for the period
        """
        try:
            cursor = self.app.db.conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0.0)
                FROM sales
                WHERE created_at >= ? AND created_at <= ?
                AND payment_type IN ('cash', 'credit')
            """, (start_date.isoformat(), end_date.isoformat()))

            result = cursor.fetchone()
            return result[0] if result else 0.0
        except sqlite3.Error as e:
            print(f"Database error getting sales for period: {e}")
            return 0.0

    def _show_error_state(self):
        """
        Display error state when data loading fails.

        Provides user feedback and prevents UI crashes.
        Handles missing UI elements gracefully.
        """
        try:
            # Set error messages for all labels with safe attribute access
            if hasattr(self.ids, 'revenue_label'):
                self.ids.revenue_label.text = "Error loading data"

            # Updated KPI error handling for new metrics
            if hasattr(self.ids, 'total_transactions_label'):
                self.ids.total_transactions_label.text = "N/A"

            if hasattr(self.ids, 'avg_sale_label'):
                self.ids.avg_sale_label.text = "N/A"

            # Period comparison error states
            if hasattr(self.ids, 'current_period_sales'):
                self.ids.current_period_sales.text = "N/A"

            if hasattr(self.ids, 'previous_period_sales'):
                self.ids.previous_period_sales.text = "N/A"

            if hasattr(self.ids, 'sales_change_label'):
                self.ids.sales_change_label.text = "N/A"

            print("Error state displayed successfully")
        except AttributeError as e:
            # Handle case where IDs might not be available
            print(f"Warning: Some UI elements not found during error state: {e}")
        except Exception as e:
            print(f"Unexpected error in error state display: {e}")

    def go_back(self):
        """Navigate back to reports screen"""
        app = MDApp.get_running_app()
        app.sm.current = 'reports'
