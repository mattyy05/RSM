"""
Inventory Report Screen - Comprehensive inventory analysis and reporting
Provides detailed product overview, sales & movement analytics, and performance metrics
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.list import OneLineListItem
from datetime import datetime, timedelta
import sqlite3


class InventoryReportScreen(MDScreen):
    """
    Dedicated screen for comprehensive inventory reporting and analysis.
    Features:
    - Product Overview (Name, Code, SKU, Category)
    - Sales & Movement tracking (Daily/Weekly/Monthly)
    - Fast/Slow moving product identification
    - Stock turnover rate calculations
    - Last sale date tracking
    - Performance optimization with caching
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.inventory_data = []  # Cache for inventory data
        self.sales_data = []  # Cache for sales data
        self.current_period = 'monthly'  # Default period: daily, weekly, monthly
        self.sort_by = 'name'  # Default sort: name, sales, turnover, last_sale
        self.filter_category = 'all'  # Category filter
        
    def on_enter(self):
        """Load inventory report data when screen is entered"""
        try:
            self.app = MDApp.get_running_app()
            
            # Check authentication and permissions
            if not self.app.auth_manager.can_access_screen('reports'):
                self.show_access_denied()
                self.app.sm.current = 'main'
                return
            
            # Log screen access
            self.app.auth_manager.log_action("ACCESS_INVENTORY_REPORT", "navigation")
            
            # Load comprehensive inventory report data
            self.load_inventory_report_data()
            self.update_navigation_permissions()
            
        except Exception as e:
            print(f"Error entering inventory report screen: {e}")
            self.show_error_message("Failed to load inventory report")
    
    def show_access_denied(self):
        """Show access denied message"""
        try:
            # Update status label if available
            if hasattr(self.ids, 'status_label'):
                self.ids.status_label.text = "Access Denied - Insufficient permissions"
                self.ids.status_label.theme_text_color = "Custom"
                self.ids.status_label.text_color = [1, 0, 0, 1]  # Red
        except Exception as e:
            print(f"Error showing access denied message: {e}")
    
    def load_inventory_report_data(self):
        """
        Load comprehensive inventory data with sales analytics
        Includes error handling and performance optimization
        """
        try:
            if not self.app or not self.app.db:
                raise Exception("Database connection not available")
            
            cursor = self.app.db.conn.cursor()
            
            # Clear existing data
            self.inventory_data = []
            self.sales_data = []
            
            # Update status
            self.update_status("Loading inventory data...")
            
            # Get comprehensive product data with sales analytics
            inventory_query = """
                SELECT 
                    p.id,
                    p.name,
                    p.category_id,
                    p.cost_price,
                    p.selling_price,
                    p.quantity,
                    p.reorder_level,
                    p.sku,
                    c.name as category,
                    p.description,
                    p.created_at,
                    p.updated_at
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name ASC
            """
            
            cursor.execute(inventory_query)
            products = cursor.fetchall()
            
            # Get sales data for each product with different time periods
            for product in products:
                product_id = product[0]
                product_data = {
                    'id': product_id,
                    'name': product[1],
                    'code': 'N/A',  # No separate code field in current schema
                    'sku': product[7] or 'N/A',  # SKU is at index 7
                    'quantity': product[5],  # quantity is at index 5
                    'cost_price': product[3],  # cost_price is at index 3
                    'selling_price': product[4],  # selling_price is at index 4
                    'low_stock_threshold': product[6] or 5,  # reorder_level is at index 6
                    'category': product[8] or 'Uncategorized',  # category from JOIN
                    'created_at': product[10],  # created_at is at index 10
                    'updated_at': product[11],  # updated_at is at index 11
                    'inventory_value': (product[3] * product[5]) if product[3] and product[5] else 0  # cost_price * quantity
                }
                
                # Calculate sales metrics
                sales_metrics = self.calculate_sales_metrics(product_id, cursor)
                product_data.update(sales_metrics)
                
                # Determine fast/slow moving status
                product_data['movement_status'] = self.determine_movement_status(sales_metrics)
                
                # Calculate stock turnover rate
                product_data['turnover_rate'] = self.calculate_turnover_rate(
                    sales_metrics, product_data['inventory_value']
                )
                
                self.inventory_data.append(product_data)
            
            # Update UI with loaded data
            self.display_inventory_report()
            self.update_summary_cards()
            self.update_status(f"Loaded {len(self.inventory_data)} products")
            
            print(f"Inventory report loaded: {len(self.inventory_data)} products")
            
        except sqlite3.Error as e:
            print(f"Database error loading inventory report: {e}")
            self.show_error_message(f"Database error: {e}")
        except Exception as e:
            print(f"Error loading inventory report data: {e}")
            self.show_error_message(f"Failed to load data: {e}")
    
    def calculate_sales_metrics(self, product_id: int, cursor):
        """
        Calculate comprehensive sales metrics for a product
        Returns dictionary with daily, weekly, monthly sales data
        """
        try:
            # Date calculations
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            metrics = {
                'daily_sales': 0,
                'weekly_sales': 0,
                'monthly_sales': 0,
                'total_sales': 0,
                'last_sale_date': None,
                'sales_frequency': 0,
                'avg_daily_sales': 0
            }
            
            # Get sales data from sale_items table
            sales_query = """
                SELECT 
                    si.quantity,
                    s.date,
                    si.total_price
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ?
                ORDER BY s.date DESC
            """
            
            cursor.execute(sales_query, (product_id,))
            sales_records = cursor.fetchall()
            
            if not sales_records:
                return metrics
            
            # Process sales records
            total_quantity = 0
            total_revenue = 0
            daily_quantity = 0
            weekly_quantity = 0
            monthly_quantity = 0
            sale_dates = []
            
            for record in sales_records:
                quantity, sale_date_str, revenue = record
                
                # Parse date (handle different date formats)
                try:
                    if isinstance(sale_date_str, str):
                        # Handle ISO format dates
                        if 'T' in sale_date_str:
                            sale_date = datetime.fromisoformat(sale_date_str).date()
                        else:
                            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d').date()
                    else:
                        sale_date = sale_date_str
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse date: {sale_date_str}")
                    continue
                
                sale_dates.append(sale_date)
                total_quantity += quantity
                total_revenue += revenue or 0
                
                # Calculate period-specific sales
                if sale_date == today:
                    daily_quantity += quantity
                if sale_date >= week_ago:
                    weekly_quantity += quantity
                if sale_date >= month_ago:
                    monthly_quantity += quantity
            
            # Update metrics
            metrics['daily_sales'] = daily_quantity
            metrics['weekly_sales'] = weekly_quantity
            metrics['monthly_sales'] = monthly_quantity
            metrics['total_sales'] = total_quantity
            metrics['total_revenue'] = total_revenue
            
            # Last sale date
            if sale_dates:
                metrics['last_sale_date'] = max(sale_dates)
                metrics['days_since_last_sale'] = (today - metrics['last_sale_date']).days
            
            # Sales frequency (sales per week over last month)
            if sale_dates:
                unique_weeks = len(set(date.isocalendar()[1] for date in sale_dates if date >= month_ago))
                metrics['sales_frequency'] = unique_weeks
                
                # Average daily sales over last 30 days
                metrics['avg_daily_sales'] = monthly_quantity / 30.0
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating sales metrics for product {product_id}: {e}")
            return {
                'daily_sales': 0,
                'weekly_sales': 0,
                'monthly_sales': 0,
                'total_sales': 0,
                'last_sale_date': None,
                'sales_frequency': 0,
                'avg_daily_sales': 0,
                'total_revenue': 0,
                'days_since_last_sale': 999
            }
    
    def determine_movement_status(self, sales_metrics):
        """
        Determine if product is fast-moving, slow-moving, or stagnant
        Based on sales frequency and recent activity
        """
        try:
            monthly_sales = sales_metrics.get('monthly_sales', 0)
            days_since_last_sale = sales_metrics.get('days_since_last_sale', 999)
            sales_frequency = sales_metrics.get('sales_frequency', 0)
            
            # Fast-moving criteria: good monthly sales and recent activity
            if monthly_sales >= 10 and days_since_last_sale <= 7:
                return "Fast-Moving"
            elif monthly_sales >= 5 and days_since_last_sale <= 14:
                return "Moderate"
            elif monthly_sales > 0 and days_since_last_sale <= 30:
                return "Slow-Moving"
            else:
                return "Stagnant"
                
        except Exception as e:
            print(f"Error determining movement status: {e}")
            return "Unknown"
    
    def calculate_turnover_rate(self, sales_metrics, inventory_value):
        """
        Calculate inventory turnover rate
        Formula: (Cost of Goods Sold) / (Average Inventory Value)
        Simplified: Monthly Sales * Cost Price / Current Inventory Value
        """
        try:
            monthly_sales = sales_metrics.get('monthly_sales', 0)
            
            if inventory_value <= 0 or monthly_sales <= 0:
                return 0.0
            
            # Estimate monthly COGS based on sales quantity and current cost
            # This is a simplified calculation - in practice, you'd use actual COGS
            monthly_cogs = monthly_sales * sales_metrics.get('cost_price', 0)
            
            # Turnover rate (annualized)
            monthly_turnover = monthly_cogs / inventory_value if inventory_value > 0 else 0
            annual_turnover = monthly_turnover * 12
            
            return round(annual_turnover, 2)
            
        except Exception as e:
            print(f"Error calculating turnover rate: {e}")
            return 0.0
    
    def display_inventory_report(self):
        """Display the inventory report in the UI with filtering and sorting"""
        try:
            if not hasattr(self.ids, 'inventory_list'):
                print("Warning: inventory_list widget not found in KV file")
                return
            
            # Clear existing items
            inventory_list = self.ids.inventory_list
            inventory_list.clear_widgets()
            
            # Apply filters and sorting
            filtered_data = self.apply_filters_and_sorting()
            
            # Display each product
            for product in filtered_data:
                product_card = self.create_product_card(product)
                inventory_list.add_widget(product_card)
            
            print(f"Displayed {len(filtered_data)} products in inventory report")
            
        except Exception as e:
            print(f"Error displaying inventory report: {e}")
    
    def apply_filters_and_sorting(self):
        """Apply current filters and sorting to inventory data"""
        try:
            filtered_data = self.inventory_data.copy()
            
            # Apply category filter
            if self.filter_category != 'all':
                filtered_data = [p for p in filtered_data if p['category'] == self.filter_category]
            
            # Apply sorting
            if self.sort_by == 'name':
                filtered_data.sort(key=lambda x: x['name'].lower())
            elif self.sort_by == 'sales':
                filtered_data.sort(key=lambda x: x['monthly_sales'], reverse=True)
            elif self.sort_by == 'turnover':
                filtered_data.sort(key=lambda x: x['turnover_rate'], reverse=True)
            elif self.sort_by == 'last_sale':
                filtered_data.sort(key=lambda x: x['days_since_last_sale'] or 999)
            elif self.sort_by == 'stock':
                filtered_data.sort(key=lambda x: x['quantity'])
            
            return filtered_data
            
        except Exception as e:
            print(f"Error applying filters and sorting: {e}")
            return self.inventory_data.copy()
    
    def create_product_card(self, product):
        """Create a comprehensive product card for the inventory report"""
        try:
            # Main card container
            card = MDCard(
                size_hint_y=None,
                height="200dp",
                elevation=2,
                padding="12dp",
                spacing="8dp",
                radius=[8, 8, 8, 8]
            )
            
            # Determine card color based on movement status
            movement_status = product['movement_status']
            if movement_status == "Fast-Moving":
                card.md_bg_color = [0.8, 1, 0.8, 1]  # Light green
            elif movement_status == "Slow-Moving":
                card.md_bg_color = [1, 1, 0.8, 1]  # Light yellow
            elif movement_status == "Stagnant":
                card.md_bg_color = [1, 0.9, 0.9, 1]  # Light red
            else:
                card.md_bg_color = [1, 1, 1, 1]  # White
            
            # Main layout matching KV file column structure
            main_layout = MDBoxLayout(
                orientation='horizontal',
                spacing="8dp",
                padding=[8, 8, 8, 8]
            )
            
            # Product Details Column (30%)
            details_column = MDBoxLayout(
                orientation='vertical',
                size_hint_x=0.3,
                spacing="2dp"
            )
            
            name_label = MDLabel(
                text=f"[b]{product['name']}[/b]",
                markup=True,
                font_style="Body1",
                halign="left",
                theme_text_color="Primary"
            )
            
            code_label = MDLabel(
                text=f"Code: {product['code']}",
                font_style="Caption",
                halign="left",
                theme_text_color="Secondary"
            )
            
            category_label = MDLabel(
                text=f"Cat: {product['category']}",
                font_style="Caption",
                halign="left",
                theme_text_color="Secondary"
            )
            
            details_column.add_widget(name_label)
            details_column.add_widget(code_label)
            details_column.add_widget(category_label)
            
            # Stock & Pricing Column (25%)
            stock_column = MDBoxLayout(
                orientation='vertical',
                size_hint_x=0.25,
                spacing="2dp"
            )
            
            # Stock level with color coding
            stock_color = [1, 0, 0, 1] if product['quantity'] <= product['low_stock_threshold'] else [0, 0.8, 0, 1]
            stock_text = f"Stock: {product['quantity']}"
            if product['quantity'] <= product['low_stock_threshold']:
                stock_text += " ⚠️"
            
            stock_label = MDLabel(
                text=stock_text,
                font_style="Body2",
                halign="center",
                theme_text_color="Custom",
                text_color=stock_color,
                bold=True
            )
            
            price_label = MDLabel(
                text=f"₱{product['selling_price']:,.2f}",
                font_style="Body2",
                halign="center",
                theme_text_color="Primary"
            )
            
            value_label = MDLabel(
                text=f"Value: ₱{product['inventory_value']:,.2f}",
                font_style="Caption",
                halign="center",
                theme_text_color="Secondary"
            )
            
            stock_column.add_widget(stock_label)
            stock_column.add_widget(price_label)
            stock_column.add_widget(value_label)
            
            # Sales Performance Column (25%)
            sales_column = MDBoxLayout(
                orientation='vertical',
                size_hint_x=0.25,
                spacing="2dp"
            )
            
            period_sales = product[f'{self.current_period}_sales']
            sales_label = MDLabel(
                text=f"{self.current_period.title()}: {period_sales}",
                font_style="Body2",
                halign="center",
                theme_text_color="Primary"
            )
            
            turnover_label = MDLabel(
                text=f"Turnover: {product['turnover_rate']:.1f}x",
                font_style="Caption",
                halign="center",
                theme_text_color="Secondary"
            )
            
            # Last sale date
            last_sale = product['last_sale_date']
            if last_sale:
                days_ago = product['days_since_last_sale']
                if days_ago == 0:
                    last_sale_text = "Today"
                elif days_ago == 1:
                    last_sale_text = "Yesterday"
                else:
                    last_sale_text = f"{days_ago}d ago"
            else:
                last_sale_text = "Never"
            
            last_sale_label = MDLabel(
                text=f"Last: {last_sale_text}",
                font_style="Caption",
                halign="center",
                theme_text_color="Secondary"
            )
            
            sales_column.add_widget(sales_label)
            sales_column.add_widget(turnover_label)
            sales_column.add_widget(last_sale_label)
            
            # Movement Status Column (20%)
            status_column = MDBoxLayout(
                orientation='vertical',
                size_hint_x=0.2,
                spacing="2dp"
            )
            
            status_label = MDLabel(
                text=f"[b]{movement_status}[/b]",
                markup=True,
                font_style="Body2",
                halign="right",
                theme_text_color="Custom",
                text_color=self.get_status_color(movement_status)
            )
            
            # Add empty labels for vertical alignment
            spacer1 = MDLabel(text="", font_style="Caption")
            spacer2 = MDLabel(text="", font_style="Caption")
            
            status_column.add_widget(status_label)
            status_column.add_widget(spacer1)
            status_column.add_widget(spacer2)
            
            # Add all columns to main layout
            main_layout.add_widget(details_column)
            main_layout.add_widget(stock_column)
            main_layout.add_widget(sales_column)
            main_layout.add_widget(status_column)
            
            card.add_widget(main_layout)
            
            return card
            
        except Exception as e:
            print(f"Error creating product card: {e}")
            # Return a simple error card
            error_card = MDCard(
                size_hint_y=None,
                height="60dp",
                padding="8dp"
            )
            error_label = MDLabel(text=f"Error displaying product: {product.get('name', 'Unknown')}")
            error_card.add_widget(error_label)
            return error_card
    
    def get_status_color(self, status):
        """Get color for movement status"""
        colors = {
            "Fast-Moving": [0, 0.8, 0, 1],      # Green
            "Moderate": [0, 0.6, 0.8, 1],       # Blue
            "Slow-Moving": [1, 0.6, 0, 1],      # Orange
            "Stagnant": [1, 0, 0, 1],           # Red
            "Unknown": [0.5, 0.5, 0.5, 1]       # Gray
        }
        return colors.get(status, [0, 0, 0, 1])
    
    def update_summary_cards(self):
        """Update summary statistics cards"""
        try:
            if not self.inventory_data:
                return
            
            # Calculate summary statistics
            total_products = len(self.inventory_data)
            total_value = sum(p['inventory_value'] for p in self.inventory_data)
            low_stock_count = sum(1 for p in self.inventory_data if p['quantity'] <= p['low_stock_threshold'])
            fast_moving_count = sum(1 for p in self.inventory_data if p['movement_status'] == 'Fast-Moving')
            stagnant_count = sum(1 for p in self.inventory_data if p['movement_status'] == 'Stagnant')
            avg_turnover = sum(p['turnover_rate'] for p in self.inventory_data) / total_products if total_products > 0 else 0
            
            # Update UI labels if they exist
            if hasattr(self.ids, 'total_products_label'):
                self.ids.total_products_label.text = str(total_products)
            
            if hasattr(self.ids, 'total_value_label'):
                self.ids.total_value_label.text = f"₱{total_value:,.2f}"
            
            if hasattr(self.ids, 'low_stock_label'):
                self.ids.low_stock_label.text = str(low_stock_count)
            
            if hasattr(self.ids, 'fast_moving_label'):
                self.ids.fast_moving_label.text = str(fast_moving_count)
            
            if hasattr(self.ids, 'stagnant_label'):
                self.ids.stagnant_label.text = str(stagnant_count)
            
            if hasattr(self.ids, 'avg_turnover_label'):
                self.ids.avg_turnover_label.text = f"{avg_turnover:.1f}x"
            
            print(f"Summary updated: {total_products} products, ₱{total_value:,.2f} total value")
            
        except Exception as e:
            print(f"Error updating summary cards: {e}")
    
    def change_period(self, period: str):
        """Change the reporting period (daily, weekly, monthly)"""
        try:
            if period in ['daily', 'weekly', 'monthly']:
                self.current_period = period
                self.display_inventory_report()  # Refresh display
                print(f"Changed reporting period to: {period}")
        except Exception as e:
            print(f"Error changing period: {e}")
    
    def change_sort(self, sort_by: str):
        """Change the sorting criteria"""
        try:
            if sort_by in ['name', 'sales', 'turnover', 'last_sale', 'stock']:
                self.sort_by = sort_by
                self.display_inventory_report()  # Refresh display
                print(f"Changed sorting to: {sort_by}")
        except Exception as e:
            print(f"Error changing sort: {e}")
    
    def filter_by_category(self, category: str):
        """Filter products by category"""
        try:
            self.filter_category = category
            self.display_inventory_report()  # Refresh display
            print(f"Filtered by category: {category}")
        except Exception as e:
            print(f"Error filtering by category: {e}")
    
    def refresh_report(self):
        """Refresh the entire inventory report"""
        try:
            self.update_status("Refreshing report...")
            self.load_inventory_report_data()
        except Exception as e:
            print(f"Error refreshing report: {e}")
            self.show_error_message("Failed to refresh report")
    
    def export_report(self):
        """Export inventory report to text file (future enhancement)"""
        try:
            # This could be enhanced to export to CSV, PDF, etc.
            print("Export functionality - placeholder for future implementation")
            self.update_status("Export feature coming soon...")
        except Exception as e:
            print(f"Error exporting report: {e}")
    
    def update_status(self, message: str):
        """Update status label"""
        try:
            if hasattr(self.ids, 'status_label'):
                self.ids.status_label.text = message
                self.ids.status_label.theme_text_color = "Secondary"
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def show_error_message(self, message: str):
        """Show error message"""
        try:
            if hasattr(self.ids, 'status_label'):
                self.ids.status_label.text = f"Error: {message}"
                self.ids.status_label.theme_text_color = "Custom"
                self.ids.status_label.text_color = [1, 0, 0, 1]  # Red
        except Exception as e:
            print(f"Error showing error message: {e}")
    
    def update_navigation_permissions(self):
        """Update navigation button visibility based on user role"""
        try:
            app = MDApp.get_running_app()
            
            if not app.auth_manager or not app.auth_manager.is_authenticated():
                return
                
            role = app.auth_manager.get_current_role()
            
            # Disable restricted buttons for cashiers
            if role == 'cashier':
                # Disable user management button
                if hasattr(self.ids, 'user_management_button'):
                    self.ids.user_management_button.disabled = True
                    self.ids.user_management_button.md_bg_color = [0.5, 0.5, 0.5, 1]
                    self.ids.user_management_button.opacity = 0.5
                    
            elif role == 'owner':
                # Enable all buttons for owners
                if hasattr(self.ids, 'user_management_button'):
                    self.ids.user_management_button.disabled = False
                    self.ids.user_management_button.md_bg_color = [0.639, 0.114, 0.114, 1]
                    self.ids.user_management_button.opacity = 1.0
                    
        except Exception as e:
            print(f"Error updating navigation permissions: {e}")
    
    def go_back(self):
        """Navigate back to reports screen"""
        try:
            app = MDApp.get_running_app()
            app.sm.current = 'reports'
        except Exception as e:
            print(f"Error navigating back: {e}")
    
    def switch_screen(self, screen_name: str):
        """Switch to a different screen with error handling"""
        try:
            app = MDApp.get_running_app()
            
            # Check if user has permission to access the screen
            if hasattr(app.auth_manager, 'can_access_screen'):
                if not app.auth_manager.can_access_screen(screen_name):
                    self.show_error_message(f"Access denied to {screen_name} screen")
                    return
            
            app.sm.current = screen_name
            print(f"Switched to {screen_name} screen")
            
        except Exception as e:
            print(f"Error switching to screen {screen_name}: {e}")
            self.show_error_message(f"Failed to switch to {screen_name}")